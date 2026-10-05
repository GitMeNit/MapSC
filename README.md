# MapSC: AI-Driven Supply Chain Vulnerability & Resiliency Engine

> **An enterprise-grade, graph-native intelligence platform designed to identify single-point failures, simulate multi-agent disruption dynamics, and compute real-time risk propagation across complex supply chain networks.**

> [!WARNING]
> **Development Status:** This project is currently under active development, contains known bugs, and is not yet fully finished or production-ready. Features, algorithms, and endpoints are subject to ongoing refinement.

---

## Executive Overview

Modern supply chains are highly interconnected networks vulnerable to cascading disruption—from raw material shortages and regional logistics bottlenecks to geopolitical shifts. **MapSC** addresses these critical failure modes by modeling supply chain ecosystems as high-dimensional, directed graph networks.

By pairing **network topology analysis** with **multi-agent simulation (MAS)**, MapSC empowers enterprise decision-makers and operations teams to test "what-if" disruption scenarios, quantify systemic vulnerabilities, and implement proactive mitigation strategies before supply chain friction impacts operational continuity.

---

## Key Capabilities & Technical Highlights

* **Graph-Native Topology Analytics**: Computes critical path dependencies, centrality metrics (Betweenness, PageRank, Eigenvector), and structural bottleneck scores across multi-tiered supplier topologies.
* **Agent-Based Disruption Simulation**: Simulates dynamic, non-linear disruption propagation—such as transport delays, tier-N supplier insolvencies, or localized production halts—across thousands of interacting nodes in real time.
* **Heterogeneous Data Ingestion Engine**: Features extensible data adapters (`adapters/` & `pipeline/`) capable of ingesting, cleaning, and unifying messy industrial records, unstructured logistics logs, and relational databases into standardized graph schemas.
* **Domain-Specific Adaptation**: Pre-configured with schema mappings and regional adapters optimized for industrial corridors, regional manufacturing hubs, and cross-border logistics lanes.
* **Full-Stack Visualization Suite**: Features a high-performance REST API backend integrated with a modern TypeScript/CSS web dashboard for real-time interactive graph exploration and scenario playback.

---

## System Architecture

```text
               +-------------------------------------------------------+
               |             Heterogeneous Data Ingestion              |
               | (Industrial Datasets, Logistics Logs, External APIs) |
               +---------------------------+---------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |            ETL & Data Pipeline (`pipeline/`)          |
               |      Entity Extraction, Normalization & Cleansing      |
               +---------------------------+---------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |            MapSC Core Engine (`core/`)                |
               |  +-----------------------+ +-----------------------+  |
               |  | Graph Network Solver  | |  Multi-Agent Swarm    |  |
               |  |  (Topology Analysis)  | |  Simulated Risk Engine|  |
               |  +-----------------------+ +-----------------------+  |
               +---------------------------+---------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |             REST API Backend (`api/`)                 |
               |     Risk Scoring, Endpoint Routing, Middleware         |
               +---------------------------+---------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |             Interactive Frontend Dashboard            |
               |       (TypeScript, CSS Graph Visualization)           |
               +-------------------------------------------------------+

```

---

## Repository Structure

```text
MapSC/
├── adapters/              # Ingestion adapters for external APIs and custom data feeds
├── api/                   # RESTful API layer, endpoints, and request routing
├── configs/               # Runtime parameters, network presets, and risk thresholds
├── core/                  # Graph engine, risk propagation algorithms, and agent logic
├── data/                  # Schema definitions, seed datasets, and sample graphs
│   ├── raw/               # Raw, unprocessed input datasets (gitignored)
│   ├── processed/         # Structured graph inputs and graph seeds (gitignored)
│   └── exports/           # Output metrics, simulation traces, and reports
├── frontend/              # Web dashboard UI (TypeScript, CSS, Graph rendering)
├── models/                # ML algorithms for risk scoring and anomaly detection
├── pipeline/              # ETL pipeline scripts for graph transformation
├── scripts/               # Automation, orchestration, and DB migration scripts
├── tests/                 # Unit, integration, and end-to-end Pytest test suite
├── KNOWN_ISSUES.md        # Tracked edge cases, performance notes, and fixes
├── conftest.py            # Global Pytest fixtures and environment configuration
├── industry.py            # Industry sector classifications and entity mapping rules
├── paths.py               # System-wide file path resolutions and data routing
├── pytest.ini             # Pytest execution settings
├── requirements.txt       # Core Python production dependencies
├── requirements-extra.txt # ML, graph analysis, and extended analytical packages
├── schema.md              # Node & Edge schema specifications and data dictionary
├── settings.py            # Global application settings and environment overrides
└── setup.ps1              # Automated environment setup script for PowerShell

```

---

## Tech Stack & Tooling

| Component | Technology | Role |
| --- | --- | --- |
| **Backend & Core Engine** | Python 3.10+ | Graph algorithms, multi-agent orchestration, REST API |
| **Graph & Data Science** | NetworkX / PyTorch Eco / Pandas / NumPy | Topology parsing, node centrality, numerical modeling |
| **Frontend UI** | TypeScript, Modern CSS, Node.js 18+ | Interactive graph rendering and simulation UI |
| **Testing & Quality** | Pytest, Flake8 / Black | Test coverage, assertion pipelines, and code formatting |
| **Environment / Tooling** | PowerShell / Bash, Virtual Environments | Automated setup and cross-platform execution |

---

## Getting Started

### Prerequisites

* **Python**: `3.10` or higher
* **Node.js**: `v18.0.0` or higher
* **Package Manager**: `pip` (Python) and `npm` (Node)

---

### Automated Environment Setup (Windows / PowerShell)

Run the automated bootstrapping script to initialize virtual environments, install core dependencies, and configure pathing:

```powershell
.\setup.ps1

```

---

### Manual Installation

#### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/GitMeNit/MapSC.git
cd MapSC

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install -r requirements-extra.txt

```

#### 2. Frontend Setup

```bash
cd frontend
npm install

```

---

## Execution Guide

### 1. Execute Data Pipeline (ETL & Graph Construction)

Process raw supplier datasets and build the underlying network graph:

```bash
python -m pipeline.run

```

### 2. Launch the REST API Backend

Start the API server to expose graph queries and simulation controls:

```bash
python -m api.main

```

### 3. Launch the Frontend Visualization Dashboard

In a separate terminal, launch the web console:

```bash
cd frontend
npm run dev

```

### 4. Run the Test Suite

Run unit and integration tests across the core graph algorithms and API endpoints:

```bash
pytest

```

---

## Data Schema Overview

For a full specification of network primitives, consult [`schema.md`](schema.md).

* **Nodes (`Entities`)**: `Supplier`, `ManufacturingPlant`, `DistributionHub`, `LogisticsCorridor`, `Retailer`
* **Edges (`Dependencies`)**: Directed links containing capacity bounds, transit latency (days), cost matrices, single-source dependency scores, and lead-time variability.

---

## Design Principles & Software Engineering Practices

* **Separation of Concerns**: Clean modular abstraction decoupling the ingestion pipeline (`pipeline/`), simulation mechanics (`core/`), API interfaces (`api/`), and UI visualization (`frontend/`).
* **Robust Error Handling**: Structured fallback strategies for missing supply chain data and resilient graph execution during missing node linkages.
* **Extensible Schema Architecture**: Designed to easily accommodate new industry domains, trade corridors, and custom risk factor scoring models.
