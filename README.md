# Katz Hyperglycemia Sodium Corrector

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Calculates corrected serum sodium for hyperglycemic patients using the Katz (1.6) and Hillier (2.4) correction formulas for DKA/HHS management.

**Correction Formulas:**
- **Katz (1973):** Corrected Na = Measured Na + 1.6 × (Glucose - 100) / 100
- **Hillier (1999):** Corrected Na = Measured Na + 2.4 × (Glucose - 100) / 100

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities

### 🔬 Core Sodium Correction
- **`calculate_corrected_sodium_katz(sodium, glucose)`** - Katz formula correction
- **`calculate_corrected_sodium_hillier(sodium, glucose)`** - Hillier formula correction
- **`calculate_metrics(**kwargs)`** - Unified interface supporting both clinical and legacy modes

### 🏥 Enterprise Features
- **Zero-PHI Outbound Interceptor:** Blocks SSNs, MRNs, phone numbers, and patient identifiers
- **HMAC-SHA256 Audit Trail:** Tamper-evident cryptographic logging
- **Multi-worker Evaluation:** QC, Safety, and Protocol Conformance workers
- **FastAPI REST API:** OpenAPI 3.1 endpoints with Prometheus metrics
- **Active Learning:** Bayesian calibration for worker reliability

---

## 📐 Mathematical Formulation

```text
Katz Correction:    corrected_na = measured_na + 1.6 * (glucose - 100) / 100
Hillier Correction: corrected_na = measured_na + 2.4 * (glucose - 100) / 100
```

**Input Validation:**
- Sodium: 100-200 mEq/L (physiological range)
- Glucose: 0-2000 mg/dL (physiological range)
- Rejects NaN, infinity, and out-of-range values

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/katz-hyperglycemia-sodium-corrector.git
cd katz-hyperglycemia-sodium-corrector

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set audit secret key (required)
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

---

## 💻 CLI Usage

### Clinical Sodium Correction (Single Patient)
```bash
# Using clinical parameters
python katz_sodium.py single --sodium 135 --glucose 450

# Legacy scoring mode
python katz_sodium.py single --v1 28.5 --v2 14.2
```

### Batch Processing
```bash
# Clinical batch (CSV with sodium, glucose columns)
python katz_sodium.py batch -i patients.csv -o corrected_results.csv
```

### Enterprise CLI (Full Platform)
```bash
# Set required environment variable
export AUDIT_SECRET_KEY="your-secure-random-key"

# Run audit evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Interactive chat with supervisor
python cli.py chat "Explain sodium correction"

# Verify audit trail integrity
python cli.py verify-audit

# Launch REST API server
python cli.py serve --host 0.0.0.0 --port 8000
```

### Input Data Schema (Batch CSV)

**Clinical Mode:**
| Field | Description | Unit |
|:------|:------------|:-----|
| sodium | Measured serum sodium | mEq/L |
| glucose | Serum glucose | mg/dL |

**Legacy Mode:**
| Field | Description |
|:------|:------------|
| v1 | Primary parameter |
| v2 | Secondary parameter |
| v3 | Tertiary parameter |

---

## 🛡️ Security Architecture

- **Zero-PHI Outbound Interceptor:** Regex-based detection and blocking of PHI patterns
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs (requires `AUDIT_SECRET_KEY`)
- **Input Validation:** Physiological range checking for clinical parameters

**⚠️ Important:** The `AUDIT_SECRET_KEY` environment variable must be set to a secure random value (minimum 16 characters) before running the enterprise features.

---

## 🧪 Testing

Run the automated test suite:

```bash
# Set audit key for tests
export AUDIT_SECRET_KEY="test-audit-key-for-development-only"

# Run all tests
pytest -v
```

Execute high-throughput simulation benchmarks:

```bash
python simulator.py 100
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
export AUDIT_SECRET_KEY="your-production-key-here"
docker-compose up --build

# Or with Docker directly
docker build -t katz-hyperglycemia-sodium-corrector .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-key" katz-hyperglycemia-sodium-corrector
```

---

## 📁 Project Structure

```
katz-hyperglycemia-sodium-corrector/
├── katz_sodium.py          # Core sodium correction algorithm
├── cli.py                  # Enterprise CLI interface
├── enrichment.py           # Enrichment feature engines
├── simulator.py            # High-throughput simulation
├── agents/
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Multi-agent orchestrator
│   ├── workers.py          # Specialized evaluation workers
│   ├── api.py              # FastAPI REST endpoints
│   ├── metrics.py          # Prometheus metrics
│   ├── learning.py         # Bayesian calibration
│   └── streamer.py         # WebSocket telemetry
├── tests/                  # Test suite
├── web/                    # Web dashboard
├── Dockerfile              # Container definition
├── docker-compose.yml      # Container orchestration
└── pyproject.toml          # Python project configuration
```
