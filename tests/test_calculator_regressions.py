"""Clinical, CSV, and audit integrity regression tests."""
import csv

import pytest

from katz_sodium import calculate_metrics, process_batch
from agents.base import AuditTrail


def test_zero_glucose_does_not_trigger_legacy_mode():
    with pytest.raises(ValueError, match="positive"):
        calculate_metrics(sodium=135, glucose=0)


@pytest.mark.parametrize("inputs", [
    {"sodium": 135}, {"glucose": 300}, {"measured_sodium": 135},
    {"measured_glucose": 300},
])
def test_incomplete_clinical_pair_is_rejected(inputs):
    with pytest.raises(ValueError, match="Both sodium and glucose"):
        calculate_metrics(**inputs)


def test_aliases_and_conventional_classification():
    normal = calculate_metrics(measured_sodium=135, measured_glucose=400)
    assert normal["katz_corrected_sodium_mEq_L"] == 139.8
    low = calculate_metrics(sodium=130, glucose=200)
    assert low["classification"] == "Hyponatremia"
    high = calculate_metrics(sodium=145, glucose=200)
    assert high["classification"] == "Hypernatremia"
    assert "treatment" in high["clinical_recommendation"].lower()


def test_case_insensitive_csv_and_original_headers(tmp_path):
    source = tmp_path / "cases.csv"
    output = tmp_path / "results.csv"
    source.write_text("CASE,Sodium,GLUCOSE\n001,135,400\n", encoding="utf-8")
    process_batch(str(source), str(output))
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["katz_corrected_sodium"] == "139.8"
    assert rows[0]["hillier_corrected_sodium"] == "142.2"
    assert rows[0]["CASE"] == "001"


def test_incomplete_clinical_csv_fails(tmp_path):
    source = tmp_path / "bad.csv"
    target = tmp_path / "out.csv"
    source.write_text("patient,sodium\nA,135\n", encoding="utf-8")
    with pytest.raises(ValueError, match="both sodium and glucose"):
        process_batch(str(source), str(target))
    assert not target.exists()


def test_bad_clinical_value_fails_without_partial_output(tmp_path):
    source = tmp_path / "bad.csv"
    target = tmp_path / "out.csv"
    source.write_text("sodium,glucose\n135,400\n136,not_a_number\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CSV row 3"):
        process_batch(str(source), str(target))
    assert not target.exists()


def test_csv_formula_injection_escaped(tmp_path):
    source = tmp_path / "bad.csv"
    target = tmp_path / "out.csv"
    source.write_text("id,sodium,glucose\n=1+1,135,400\n", encoding="utf-8")
    process_batch(str(source), str(target))
    with target.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["id"] == "'=1+1"


def test_refuse_to_overwrite_csv_source(tmp_path):
    file = tmp_path / "in.csv"
    file.write_text("sodium,glucose\n135,400\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must differ"):
        process_batch(str(file), str(file))


def test_audit_chain_recomputes_hmac():
    trail = AuditTrail(secret_key="independent-test-secret-value")
    trail.log("operator", "staff", "EVALUATION", {"status": "pass"})
    assert trail.verify_integrity()
    copy = trail.get_trail()
    copy[0]["actor"] = "another-operator"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "another-operator"
    assert not trail.verify_integrity()


def test_production_requires_audit_secret(monkeypatch):
    monkeypatch.delenv("AUDIT_SECRET_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(ValueError, match="required in production"):
        AuditTrail()


def test_fastapi_clinical_route_function():
    from fastapi import HTTPException
    from agents.api import SodiumRequest, api_corrected_sodium

    actual = api_corrected_sodium(SodiumRequest(sodium=135, glucose=400))
    assert actual["katz_corrected_sodium_mEq_L"] == 139.8
    with pytest.raises(HTTPException) as err:
        api_corrected_sodium(SodiumRequest(sodium=135, glucose=0))
    assert err.value.status_code == 422


def test_unimplemented_llm_provider_is_not_silently_mocked():
    from agents.llm_factory import LLMFactory
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")
