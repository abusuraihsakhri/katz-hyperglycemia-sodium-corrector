import pytest
from katz_sodium import (
    calculate_metrics, process_batch,
    calculate_corrected_sodium_katz, calculate_corrected_sodium_hillier,
    validate_sodium, validate_glucose,
    KATZ_MULTIPLIER, HILLIER_MULTIPLIER, GLUCOSE_NORMAL
)


def test_katz_sodium_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_katz_sodium_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


# =============================================================================
# Katz Formula Tests
# =============================================================================

def test_katz_formula_normal_glucose():
    """At normal glucose (100), corrected sodium equals measured sodium."""
    result = calculate_corrected_sodium_katz(140.0, 100.0)
    assert result == 140.0


def test_katz_formula_mild_hyperglycemia():
    """Test Katz correction with mild hyperglycemia."""
    # Na=135, Glucose=200
    # Expected: 135 + 1.6 * (200-100)/100 = 135 + 1.6 = 136.6
    result = calculate_corrected_sodium_katz(135.0, 200.0)
    assert result == 136.6


def test_katz_formula_severe_hyperglycemia():
    """Test Katz correction with severe hyperglycemia (DKA)."""
    # Na=130, Glucose=500
    # Expected: 130 + 1.6 * (500-100)/100 = 130 + 6.4 = 136.4
    result = calculate_corrected_sodium_katz(130.0, 500.0)
    assert result == 136.4


# =============================================================================
# Hillier Formula Tests
# =============================================================================

def test_hillier_formula_normal_glucose():
    """At normal glucose (100), corrected sodium equals measured sodium."""
    result = calculate_corrected_sodium_hillier(140.0, 100.0)
    assert result == 140.0


def test_hillier_formula_mild_hyperglycemia():
    """Test Hillier correction with mild hyperglycemia."""
    # Na=135, Glucose=200
    # Expected: 135 + 2.4 * (200-100)/100 = 135 + 2.4 = 137.4
    result = calculate_corrected_sodium_hillier(135.0, 200.0)
    assert result == 137.4


def test_hillier_formula_severe_hyperglycemia():
    """Test Hillier correction with severe hyperglycemia (HHS)."""
    # Na=128, Glucose=600
    # Expected: 128 + 2.4 * (600-100)/100 = 128 + 12.0 = 140.0
    result = calculate_corrected_sodium_hillier(128.0, 600.0)
    assert result == 140.0


# =============================================================================
# calculate_metrics Clinical Mode Tests
# =============================================================================

def test_calculate_metrics_clinical_mode():
    """Test calculate_metrics with clinical sodium/glucose parameters."""
    res = calculate_metrics(sodium=135.0, glucose=400.0)
    assert "katz_corrected_sodium_mEq_L" in res
    assert "hillier_corrected_sodium_mEq_L" in res
    assert res["measured_sodium_mEq_L"] == 135.0
    assert res["glucose_mg_dL"] == 400.0
    # Katz: 135 + 1.6 * (400-100)/100 = 135 + 4.8 = 139.8
    assert res["katz_corrected_sodium_mEq_L"] == 139.8
    # Hillier: 135 + 2.4 * (400-100)/100 = 135 + 7.2 = 142.2
    assert res["hillier_corrected_sodium_mEq_L"] == 142.2


def test_calculate_metrics_hyponatremia_classification():
    """Test that low corrected sodium is classified as hyponatremia."""
    res = calculate_metrics(sodium=125.0, glucose=150.0)
    assert res["classification"] == "Hyponatremia"


def test_calculate_metrics_hypernatremia_classification():
    """Test that high corrected sodium is classified as hypernatremia."""
    res = calculate_metrics(sodium=155.0, glucose=150.0)
    assert res["classification"] == "Hypernatremia"


def test_calculate_metrics_normal_classification():
    """Test that normal corrected sodium is classified correctly."""
    res = calculate_metrics(sodium=140.0, glucose=100.0)
    assert res["classification"] == "Normal corrected sodium"


# =============================================================================
# Input Validation Tests
# =============================================================================

def test_validate_sodium_valid():
    """Test sodium validation with valid values."""
    assert validate_sodium(135.0) == 135.0
    assert validate_sodium(100.0) == 100.0  # boundary
    assert validate_sodium(200.0) == 200.0  # boundary


def test_validate_sodium_invalid():
    """Test sodium validation rejects invalid values."""
    with pytest.raises(ValueError, match="outside physiological range"):
        validate_sodium(50.0)
    with pytest.raises(ValueError, match="outside physiological range"):
        validate_sodium(250.0)


def test_validate_sodium_nan_inf():
    """Test sodium validation rejects NaN and infinity."""
    with pytest.raises(ValueError, match="finite number"):
        validate_sodium(float('nan'))
    with pytest.raises(ValueError, match="finite number"):
        validate_sodium(float('inf'))


def test_validate_glucose_valid():
    """Test glucose validation with valid values."""
    assert validate_glucose(100.0) == 100.0
    assert validate_glucose(500.0) == 500.0


def test_validate_glucose_invalid():
    """Test glucose validation rejects invalid values."""
    with pytest.raises(ValueError, match="positive"):
        validate_glucose(-10.0)
    with pytest.raises(ValueError, match="positive"):
        validate_glucose(0.0)
    with pytest.raises(ValueError, match="exceeds maximum"):
        validate_glucose(3000.0)


# =============================================================================
# Batch Processing with Clinical Data
# =============================================================================

def test_clinical_batch_processing(tmp_path):
    """Test batch processing with clinical sodium/glucose columns."""
    csv_in = tmp_path / "clinical_in.csv"
    csv_out = tmp_path / "clinical_out.csv"
    csv_in.write_text(
        "Patient_ID,sodium,glucose\n"
        "PT-101,135,450\n"
        "PT-102,142,120\n",
        encoding="utf-8"
    )
    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "katz_corrected_sodium" in content
    assert "hillier_corrected_sodium" in content


# =============================================================================
# Constants Verification
# =============================================================================

def test_katz_multiplier_value():
    """Verify Katz multiplier is 1.6."""
    assert KATZ_MULTIPLIER == 1.6


def test_hillier_multiplier_value():
    """Verify Hillier multiplier is 2.4."""
    assert HILLIER_MULTIPLIER == 2.4


def test_glucose_normal_reference():
    """Verify normal glucose reference is 100 mg/dL."""
    assert GLUCOSE_NORMAL == 100.0
