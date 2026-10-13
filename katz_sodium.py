#!/usr/bin/env python3
"""
Katz & Hillier Corrected Sodium for Hyperglycemia
Calculates corrected serum sodium using Katz (1.6) and Hillier (2.4) multipliers for DKA/HHS management.

The correction formulas adjust measured serum sodium for hyperglycemia:
- Katz (1973): Corrected Na = Measured Na + 1.6 * (Glucose - 100) / 100
- Hillier (1999): Corrected Na = Measured Na + 2.4 * (Glucose - 100) / 100

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional


# Clinical constants
KATZ_MULTIPLIER = 1.6  # mEq/L per 100 mg/dL glucose above normal
HILLIER_MULTIPLIER = 2.4  # mEq/L per 100 mg/dL glucose above normal
GLUCOSE_NORMAL = 100.0  # mg/dL, normal glucose reference
GLUCOSE_MAX = 2000.0  # mg/dL, physiological upper bound
SODIUM_MIN = 100.0  # mEq/L, physiological lower bound
SODIUM_MAX = 200.0  # mEq/L, physiological upper bound


def validate_sodium(sodium: float) -> float:
    """Validate measured sodium is within physiological range."""
    if math.isnan(sodium) or math.isinf(sodium):
        raise ValueError("Sodium value must be a finite number")
    if not (SODIUM_MIN <= sodium <= SODIUM_MAX):
        raise ValueError(
            f"Measured sodium {sodium:.1f} mEq/L outside physiological range "
            f"[{SODIUM_MIN:.0f}-{SODIUM_MAX:.0f}]"
        )
    return sodium


def validate_glucose(glucose: float) -> float:
    """Validate glucose is within physiological range."""
    if math.isnan(glucose) or math.isinf(glucose):
        raise ValueError("Glucose value must be a finite number")
    if glucose <= 0:
        raise ValueError("Glucose value must be positive")
    if glucose > GLUCOSE_MAX:
        raise ValueError(
            f"Glucose {glucose:.1f} mg/dL exceeds maximum physiological bound ({GLUCOSE_MAX:.0f})"
        )
    return glucose


def calculate_corrected_sodium_katz(measured_sodium: float, glucose: float) -> float:
    """
    Calculate corrected sodium using Katz formula (1973).
    Corrected Na = Measured Na + 1.6 * (Glucose - 100) / 100
    """
    validate_sodium(measured_sodium)
    validate_glucose(glucose)
    correction = KATZ_MULTIPLIER * (glucose - GLUCOSE_NORMAL) / 100.0
    return round(measured_sodium + correction, 2)


def calculate_corrected_sodium_hillier(measured_sodium: float, glucose: float) -> float:
    """
    Calculate corrected sodium using Hillier formula (1999).
    Corrected Na = Measured Na + 2.4 * (Glucose - 100) / 100
    """
    validate_sodium(measured_sodium)
    validate_glucose(glucose)
    correction = HILLIER_MULTIPLIER * (glucose - GLUCOSE_NORMAL) / 100.0
    return round(measured_sodium + correction, 2)


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for katz-hyperglycemia-sodium-corrector.

    Accepts either:
    - Clinical mode: sodium and glucose parameters (Katz/Hillier correction)
    - Legacy mode: v1, v2, v3 parameters (generic scoring)
    """
    # Check if clinical parameters are provided
    sodium = kwargs.get("sodium")
    if sodium is None:
        sodium = kwargs.get("measured_sodium")
    glucose = kwargs.get("glucose")
    if glucose is None:
        glucose = kwargs.get("measured_glucose")

    # Never silently fall back to unrelated legacy scoring when one
    # clinical measurement is omitted or invalid (including zero).
    if sodium is not None or glucose is not None:
        if sodium is None or glucose is None:
            raise ValueError("Both sodium and glucose are required for clinical correction")
        return _calculate_clinical_metrics(float(sodium), float(glucose))

    # Legacy generic scoring mode
    return _calculate_legacy_metrics(**kwargs)


def _calculate_clinical_metrics(sodium: float, glucose: float) -> Dict[str, Any]:
    """Calculate corrected sodium using both Katz and Hillier formulas."""
    validate_sodium(sodium)
    validate_glucose(glucose)

    katz_corrected = calculate_corrected_sodium_katz(sodium, glucose)
    hillier_corrected = calculate_corrected_sodium_hillier(sodium, glucose)

    # Clinical interpretation
    if katz_corrected < 135:
        classification = "Hyponatremia"
    elif katz_corrected > 145:
        classification = "Hypernatremia"
    else:
        classification = "Normal corrected sodium"
    recommendation = (
        "Estimated correction only; interpret with clinical context, "
        "serial electrolytes, tonicity, and volume status. "
        "Do not base treatment solely on this result."
    )

    return {
        "tool": "katz-hyperglycemia-sodium-corrector",
        "measured_sodium_mEq_L": sodium,
        "glucose_mg_dL": glucose,
        "katz_corrected_sodium_mEq_L": katz_corrected,
        "hillier_corrected_sodium_mEq_L": hillier_corrected,
        "katz_multiplier": KATZ_MULTIPLIER,
        "hillier_multiplier": HILLIER_MULTIPLIER,
        "classification": classification,
        "clinical_recommendation": recommendation,
    }


def _calculate_legacy_metrics(**kwargs) -> Dict[str, Any]:
    """Legacy generic scoring for backward compatibility."""
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                params[k] = float(v)
            except (ValueError, TypeError):
                params[k] = str(v)

    numeric_vals = [val for val in params.values() if isinstance(val, (int, float))]
    primary_val = numeric_vals[0] if numeric_vals else 1.0

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)

    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "katz-hyperglycemia-sodium-corrector",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def process_batch(input_csv: str, output_csv: str) -> None:
    if __import__("os").path.abspath(input_csv) == __import__("os").path.abspath(output_csv):
        raise ValueError("Input and output CSV paths must differ")
    with open(input_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    # CSV headers are handled case-insensitively; incomplete clinical
    # datasets must fail rather than producing misleading legacy scores.
    normalized_headers = [name.strip().lower() for name in fieldnames]
    if not fieldnames or len(normalized_headers) != len(set(normalized_headers)):
        raise ValueError("CSV requires non-duplicate column headers")
    has_sodium = any(name in normalized_headers for name in ("sodium", "measured_sodium"))
    has_glucose = any(name in normalized_headers for name in ("glucose", "measured_glucose"))
    if has_sodium != has_glucose:
        raise ValueError("Clinical CSV requires both sodium and glucose columns")
    is_clinical = has_sodium and has_glucose

    result_fields = ([
        "katz_corrected_sodium", "hillier_corrected_sodium",
        "classification", "clinical_recommendation"
    ] if is_clinical else ["score", "classification", "clinical_recommendation"])
    out_fields = fieldnames + [name for name in result_fields if name not in fieldnames]
    out_rows = []

    for index, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(f"CSV row {index} contains more values than headers")
        normalized = {key.strip().lower(): value for key, value in row.items()}
        try:
            if is_clinical:
                sodium = normalized.get("sodium", normalized.get("measured_sodium"))
                glucose = normalized.get("glucose", normalized.get("measured_glucose"))
                if not sodium or not glucose:
                    raise ValueError("Missing sodium or glucose")
                calc_res = calculate_metrics(sodium=sodium, glucose=glucose)
            else:
                calc_res = calculate_metrics(**normalized)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid data in CSV row {index}: {exc}") from exc

        # Prevent cells supplied by untrusted CSVs from executing formulas
        # when opened in spreadsheet software.
        row_dict = {
            key: ("'" + value if isinstance(value, str)
                  and value.lstrip().startswith(("=", "+", "-", "@")) else value)
            for key, value in row.items()
        }
        if is_clinical:
            row_dict["katz_corrected_sodium"] = calc_res["katz_corrected_sodium_mEq_L"]
            row_dict["hillier_corrected_sodium"] = calc_res["hillier_corrected_sodium_mEq_L"]
        else:
            row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Katz & Hillier Corrected Sodium for Hyperglycemia")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser - clinical mode
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--sodium", type=float, help="Measured serum sodium (mEq/L)")
    single_parser.add_argument("--glucose", type=float, help="Serum glucose (mg/dL)")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter (legacy mode)")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter (legacy mode)")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter (legacy mode)")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
