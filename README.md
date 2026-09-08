# Veda-Technology-Day16
# ⚡ DataOps Pro | Enterprise Job Orchestrator

Enterprise-grade Scheduled Python Data Pipeline & Monitoring Suite built with Streamlit, Pandas, and Schedule.

## 🚀 Features
* **Automated Data Pipelines:** Schedule background jobs to fetch real-time financial asset metrics (CoinGecko API).
* **Robust Error Handling & Retries:** Configurable retry limits with fallback logging and webhook alerts (Discord/Slack).
* **Interactive Dashboard:** Real-time data visualization via Plotly, key performance indicators (KPIs), and log monitors.
* **Modular Architecture:** Clean separation of concerns between core pipeline jobs (`job.py`) and the web interface (`app.py`).

---

## 📂 Project Structure
```text
Day-16/
│
├── app.py              # Streamlit frontend dashboard & background scheduler
├── job.py              # Standalone data extraction, retry logic & file logging
├── job_config.json     # Configuration parameters (Assets, Webhooks, Retries)
├── output_report.csv   # Target dataset storing execution history and prices
└── execution_logs.log  # Live execution terminal stream logs
