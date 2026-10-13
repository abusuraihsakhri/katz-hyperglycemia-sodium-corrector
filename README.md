# Katz Hyperglycemia Sodium Corrector

Calculate estimated serum sodium in hyperglycemia using the **Katz (1.6)** and **Hillier (2.4)** correction factors. The repository includes a dependency-free Python calculator and CSV processor, a standalone browser calculator, and a separate FastAPI audit-service interface.

## Browser application

Open [web/index.html](web/index.html) locally in a modern browser. The static calculator is designed for GitHub Pages; the publishing workflow is in [pages.yml](.github/workflows/pages.yml). A live URL will be listed here only after the deployment is verified.

Enter measured serum sodium in **mEq/L** and glucose in **mg/dL**, then select **Calculate**. The page displays both corrected sodium estimates, their difference, and a Katz-based comparison with the conventional adult sodium reference interval of 135–145 mEq/L.

The browser calculator requires no Python, backend, account, or external scripts. It performs the computation locally without sending or saving inputs. It supports keyboard navigation and small screens. It has no batch upload interface; use the Python CLI for CSV input.

## Formula and scope

For glucose in mg/dL:

```text
Corrected sodium (mEq/L) = measured sodium + factor × (glucose − 100) / 100
Katz factor:   1.6 mEq/L per 100 mg/dL
Hillier factor: 2.4 mEq/L per 100 mg/dL
```

Example: measured Na = 135 mEq/L, glucose = 400 mg/dL yields **139.8 mEq/L (Katz)** and **142.2 mEq/L (Hillier)**.

Input bounds in the Python implementation: measured sodium 100–200 mEq/L and glucose >0–2000 mg/dL. The browser UI is restricted to glucose 100–2000 mg/dL because the correction is intended for hyperglycemia. These are software validation limits, **not clinical safety thresholds**.

**Clinical limitation:** These are estimates, not direct measurements of true sodium at euglycemia. The Hillier study found nonlinearity, particularly when glucose exceeded 400 mg/dL; fixed correction factors are therefore approximations. Consider measured and serial sodium, osmolality/tonicity, volume status, and the full clinical context. Do not use this calculator as a treatment protocol or to determine fluid/hypertonic saline therapy.

Primary literature:
- Katz MA. *Hyperglycemia-induced hyponatremia—calculation of expected serum sodium depression.* N Engl J Med. 1973;289:843–844. [doi:10.1056/NEJM197310182891607](https://doi.org/10.1056/NEJM197310182891607)
- Hillier TA, Abbott RD, Barrett EJ. *Hyponatremia: evaluating the correction factor for hyperglycemia.* Am J Med. 1999;106:399–403. [doi:10.1016/S0002-9343(99)00055-8](https://doi.org/10.1016/S0002-9343(99)00055-8)

## Python use

Requires Python 3.10 or newer.

```bash
python -m pip install -e ".[dev]"
python katz_sodium.py single --sodium 135 --glucose 400
python katz_sodium.py batch --input sample.csv --output results.csv
python -m pytest -q
```

The module also exposes `calculate_corrected_sodium_katz`, `calculate_corrected_sodium_hillier`, and `calculate_metrics`. For backward compatibility, `calculate_metrics(v1=..., v2=...)` and legacy CSV fields remain supported, but **should not be interpreted as corrected sodium**. Clinical input requires both sodium and glucose. Clinical CSV column names are case-insensitive and accept `sodium/glucose` or `measured_sodium/measured_glucose`.

## Optional API and audit service

```bash
export AUDIT_SECRET_KEY="replace-with-a-unique-random-secret"
python cli.py serve --host 127.0.0.1 --port 8000
```

- `POST /api/corrected-sodium`: JSON `{"sodium":135,"glucose":400}`; returns both correction estimates.
- `GET /health`: basic service status.
- `POST /api/audit` and `GET /api/audit/logs`: separate generic task assessment and in-memory HMAC audit trail.
- `POST /api/chat`: deterministic mock response, **not an actual clinical or LLM consultation**.

The auxiliary generic task workers use illustrative numerical thresholds and **must not be used as validated medical triage rules**. PHI detection uses a limited set of patterns and does **not** constitute HIPAA de-identification. Avoid entering patient identifiers into the API or CSV files.

Set a secret key of at least 16 characters for audit signing. The application warns when it uses a development-only fallback; setting `ENVIRONMENT=production` prevents that fallback. The Docker Compose configuration requires an explicit `AUDIT_SECRET_KEY`.

```bash
AUDIT_SECRET_KEY="replace-with-a-unique-random-secret" docker compose up --build
```

## Development and tests

- `python -m pytest -q`: clinical, audit, legacy, and enrichment regression tests.
- `node --check web/app.js && node tests/browser_smoke.cjs`: JavaScript syntax and simulated browser interaction smoke checks (Node.js needed only for tests).
- GitHub Actions runs the Python test matrix and browser checks on pull requests and pushes to the main branch.

The browser calculator has no Python/WASM runtime because straightforward arithmetic can be executed directly in JavaScript. The API and audit service require a Python server and cannot run on static GitHub Pages. The browser UI works on current Chromium, Firefox, and Safari-derived browsers; extensive device-specific testing has not been performed.

## License

[MIT](LICENSE).
