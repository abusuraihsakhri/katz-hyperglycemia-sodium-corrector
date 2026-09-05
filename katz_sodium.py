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
    sodium = kwargs.get("sodium") or kwargs.get("measured_sodium")
    glucose = kwargs.get("glucose") or kwargs.get("measured_glucose")

    if sodium is not None and glucose is not None:
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
    if katz_corrected < 130:
        classification = "Hyponatremia"
        recommendation = "Evaluate volume status; consider free water restriction or hypertonic saline per protocol"
    elif katz_corrected > 150:
        classification = "Hypernatremia"
        recommendation = "Evaluate for dehydration; gradual free water replacement recommended"
    else:
        classification = "Normal corrected sodium"
        recommendation = "Continue monitoring; corrected sodium within normal range"

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
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    # Detect if this is a clinical batch (has sodium/glucose columns)
    fieldnames_lower = [f.lower() for f in fieldnames]
    is_clinical = "sodium" in fieldnames_lower and "glucose" in fieldnames_lower

    if is_clinical:
        out_fields = fieldnames + [
            "katz_corrected_sodium", "hillier_corrected_sodium",
            "classification", "clinical_recommendation"
        ]
    else:
        out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]

    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        if is_clinical:
            row_dict["katz_corrected_sodium"] = calc_res.get("katz_corrected_sodium_mEq_L", "")
            row_dict["hillier_corrected_sodium"] = calc_res.get("hillier_corrected_sodium_mEq_L", "")
        else:
            row_dict["score"] = calc_res.get("score", "")
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
