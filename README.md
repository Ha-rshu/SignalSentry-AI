# 🛡️ SignalSentry AI

### From suspicious signals to explainable intelligence.

**SignalSentry AI** is a cybersecurity threat-intelligence investigation platform designed to help analysts examine suspicious digital activity, explore evidence, and understand potential threat indicators through an interactive command-center interface.

Built as a project for the **Meta Global AI Developer Hackathon 2026**.

> 🚧 **Development status:** Prototype in progress. The current version uses synthetic demonstration data and transparent local rule-based analysis. The autonomous investigation engine and Meta model integration are planned future milestones, not currently implemented.

---

## ✨ Overview

SignalSentry AI aims to make digital threat investigation more structured, visual, and explainable.

The prototype provides an analyst-oriented workspace for exploring synthetic records, identifying suspicious indicators, examining supported relationships, and reviewing investigation findings.

## 🚀 Current Features

- **Command Center:** Overview of records, suspicious indicators, data quality, and investigation activity.
- **Investigation Workspace:** Submit an investigation goal and run the current local rule-based analysis.
- **Threat Intelligence:** Explore synthetic records and their matched indicators.
- **Network Intelligence:** Visualize observed relationships between records, platforms, and matched rule labels.
- **Investigation Reports:** Review evidence-backed findings and mark reports as reviewed by an analyst.
- **Data Explorer:** Explore and filter the demonstration dataset.
- **Data Validation:** Identify missing fields, duplicate IDs, invalid timestamps, and other data-quality issues.
- **CSV Export:** Export available analysis data.

## 🧠 How It Works Today

The current prototype follows a local analysis workflow:

1. Load synthetic demonstration records.
2. Validate the dataset.
3. Apply transparent keyword-based analysis rules.
4. Display suspicious indicators and supporting records.
5. Visualize supported record relationships.
6. Generate a report for human review.

**Note:** The current prototype does not connect to live social-media feeds or an external AI model.

## 🏗️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive dashboard |
| Pandas | Data processing |
| Plotly | Data visualization |
| NetworkX | Relationship graph analysis |
| Pytest | Automated testing |

## 📂 Project Structure

```text
SignalSentry-AI/
│
├── app/
│   ├── main.py
│   ├── dashboard.py
│   ├── analyzer.py
│   ├── data_loader.py
│   ├── agent.py
│   └── config.py
│
├── data/
│   └── sample_posts.csv
│
├── tests/
│   └── test_smoke.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/SignalSentry-AI.git
cd SignalSentry-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch the application

```bash
python -m streamlit run app/main.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

## 🧪 Run Tests

Run the automated test suite:

```bash
python -m pytest -q
```

The latest reported test result during development was **9 passed**.

## 🔐 Safety and Responsible Use

- The current demonstration dataset is synthetic.
- The prototype does not establish the real-world identity or intent of any person.
- Suspicious indicators are heuristic signals, not proof of malicious activity.
- Network visualizations show only relationships supported by available fields.
- Investigation findings are intended for human review.
- No automatic enforcement or public accusations are performed.

## 🗺️ Development Roadmap

- [x] Initial Streamlit application
- [x] Synthetic dataset and local analysis
- [x] Data validation and integrity checks
- [x] Command-center dashboard
- [x] Evidence and network visualization
- [x] Investigation report and analyst review
- [ ] Single-agent investigation engine
- [ ] Bounded tool execution and evidence validation
- [ ] Authorized Meta model integration, subject to API access
- [ ] Expanded evaluation and final demonstration

## 🎯 Project Vision

The long-term vision is to develop an explainable, human-supervised threat-intelligence assistant that can plan investigations, use analytical tools, correlate evidence, and produce structured intelligence reports.

## 👩‍💻 Author

**Harshita Pandey**

B.Tech Computer Science & Engineering

Interested in Cybersecurity, Artificial Intelligence, and Agentic AI.

---

*Built with curiosity, experimentation, and a focus on responsible AI-powered security investigation.*