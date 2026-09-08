from datetime import datetime, timedelta
import json
import os
import threading
import time
import pandas as pd
import plotly.express as px
import schedule
import streamlit as st

st.set_page_config(
    page_title="DataOps Pro | Enterprise Job Orchestrator",
    page_icon="⚡",
    layout="wide",
)

# --- CONFIGURATION & FILES ---
DATA_FILE = "output_report.csv"
LOG_FILE = "execution_logs.log"
CONFIG_FILE = "job_config.json"

if not os.path.exists(CONFIG_FILE):
  initial_config = {
      "coins": ["bitcoin", "ethereum", "cardano", "solana"],
      "webhook_url": "",
      "max_retries": 3,
  }
  with open(CONFIG_FILE, "w") as f:
    json.dump(initial_config, f)


def load_config():
  try:
    with open(CONFIG_FILE, "r") as f:
      return json.load(f)
  except:
    return {
        "coins": ["bitcoin", "ethereum"],
        "webhook_url": "",
        "max_retries": 3,
    }


def log_message(message):
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  formatted_msg = f"{timestamp} - {message}"
  print(formatted_msg)
  with open(LOG_FILE, "a") as f:
    f.write(formatted_msg + "\n")


def send_webhook_alert(message, webhook_url):
  import requests

  if not webhook_url:
    return
  try:
    payload = {
        "content": (
            "🚨 **[PIPELINE FAILURE]**: Scheduled job failed after retries.\nError:"
            f" `{message}`"
        )
    }
    requests.post(webhook_url, json=payload, timeout=5)
    log_message("Webhook notification sent successfully.")
  except Exception as e:
    log_message(f"Failed to transmit webhook alert: {e}")


# --- CORE JOB FUNCTION ---
def run_scheduled_job():
  import requests

  start_time = time.time()
  config = load_config()
  coins = config.get("coins", ["bitcoin", "ethereum"])
  webhook_url = config.get("webhook_url", "")
  max_retries = config.get("max_retries", 3)

  log_message(f"Job started tracking assets: {coins}")

  attempt = 0
  success = False

  while attempt < max_retries and not success:
    try:
      coin_str = ",".join(coins)
      url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_str}&vs_currencies=usd"
      response = requests.get(url, timeout=10)

      if response.status_code != 200:
        raise Exception(f"API Error: HTTP Status Code {response.status_code}")

      data = response.json()
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      new_row = {"Timestamp": timestamp}
      for coin in coins:
        new_row[f"{coin.capitalize()}_USD"] = (
            data.get(coin, {}).get("usd", 0.0)
        )

      duration = round(time.time() - start_time, 2)
      new_row["Duration_Sec"] = duration
      new_row["Status"] = "SUCCESS"

      df_new = pd.DataFrame([new_row])

      if os.path.exists(DATA_FILE):
        df_existing = pd.read_csv(DATA_FILE)
        if (
            not df_existing.empty
            and timestamp in df_existing["Timestamp"].values
        ):
          log_message("Duplicate execution detected. Skipping save.")
          return True
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
      else:
        df_final = df_new

      df_final.to_csv(DATA_FILE, index=False)
      log_message(f"Pipeline executed successfully in {duration} seconds.")
      success = True
      return True

    except Exception as e:
      attempt += 1
      error_msg = f"Attempt {attempt}/{max_retries} failed: {str(e)}"
      log_message(error_msg)

      if attempt >= max_retries:
        send_webhook_alert(str(e), webhook_url)
        duration = round(time.time() - start_time, 2)

        fail_row = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        for coin in coins:
          fail_row[f"{coin.capitalize()}_USD"] = 0.0
        fail_row["Duration_Sec"] = duration
        fail_row["Status"] = f"FAILED: {str(e)}"

        df_fail = pd.DataFrame([fail_row])
        if os.path.exists(DATA_FILE):
          df_existing = pd.read_csv(DATA_FILE)
          for col in df_existing.columns:
            if col not in df_fail.columns:
              df_fail[col] = 0.0
          pd.concat([df_existing, df_fail], ignore_index=True).to_csv(
              DATA_FILE, index=False
          )
        else:
          df_fail.to_csv(DATA_FILE, index=False)
      else:
        time.sleep(2)


# --- BACKGROUND SCHEDULER THREAD ---
if "scheduler_running" not in st.session_state:
  st.session_state.scheduler_running = False
if "next_run_time" not in st.session_state:
  st.session_state.next_run_time = None


def run_background_scheduler(interval_minutes):
  schedule.clear()
  schedule.every(interval_minutes).minutes.do(run_scheduled_job)
  st.session_state.next_run_time = datetime.now() + timedelta(
      minutes=interval_minutes
  )
  while st.session_state.scheduler_running:
    schedule.run_pending()
    time.sleep(1)


# --- UI DASHBOARD INTERFACE ---
st.markdown(
    """
    <div style="padding: 20px; background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%); border-radius: 12px; color: white; margin-bottom: 25px;">
        <h1 style="margin:0; font-size: 2.2rem;">⚡ DataOps Orchestrator Pro</h1>
        <p style="margin:5px 0 0 0; font-size: 1.1rem; opacity: 0.9;">Enterprise-grade Scheduled Python Data Pipeline & Monitoring Suite</p>
    </div>
    """,
    unsafe_allow_html=True,
)

config_data = load_config()

st.sidebar.header("🎛️ Control Center")
selected_coins = st.sidebar.multiselect(
    "Target Assets Tracking",
    ["bitcoin", "ethereum", "cardano", "solana", "dogecoin", "ripple", "polygon"],
    default=config_data.get("coins", ["bitcoin", "ethereum"]),
)

webhook_input = st.sidebar.text_input(
    "Discord / Slack Webhook URL",
    value=config_data.get("webhook_url", ""),
    type="password",
)
max_retries_input = st.sidebar.slider("Failure Retry Limit", 1, 5, 3)

if st.sidebar.button("💾 Apply Configuration"):
  updated_config = {
      "coins": selected_coins,
      "webhook_url": webhook_input,
      "max_retries": max_retries_input,
  }
  with open(CONFIG_FILE, "w") as f:
    json.dump(updated_config, f)
  st.sidebar.success("Settings saved successfully!")

st.sidebar.divider()
st.sidebar.subheader("🚀 Job Execution Actions")

if st.sidebar.button("⚡ Execute Pipeline Now", type="primary"):
  with st.spinner("Running scheduled data job..."):
    run_scheduled_job()
  st.sidebar.success("Job run complete!")
  st.rerun()

interval = st.sidebar.number_input(
    "Automation Interval (Minutes)", 1, 60, 5
)

if not st.session_state.scheduler_running:
  if st.sidebar.button("▶️ Start Background Automation"):
    if not selected_coins:
      st.sidebar.error("Select at least one asset to track.")
    else:
      st.session_state.scheduler_running = True
      threading.Thread(
          target=run_background_scheduler, args=(interval,), daemon=True
      ).start()
      st.sidebar.success("Background scheduler started!")
      st.rerun()
else:
  st.sidebar.warning("🟢 Scheduler is ACTIVE & Running")
  if st.session_state.next_run_time:
    time_left = str(st.session_state.next_run_time - datetime.now()).split(".")[
        0
    ]
    st.sidebar.info(f"⏳ Next Run In: approx {time_left}")
  if st.sidebar.button("⏹️ Stop Automation"):
    st.session_state.scheduler_running = False
    schedule.clear()
    st.sidebar.info("Scheduler deactivated.")
    st.rerun()

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Analytics & KPIs",
    "📊 Dataset Explorer",
    "📜 Live Terminal Logs",
    "💡 Technical Overview",
])

with tab1:
  st.subheader("Real-Time Financial & Pipeline Analytics")
  if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    success_df = df[df["Status"] == "SUCCESS"]

    if not success_df.empty:
      total_runs = len(df)
      success_runs = len(success_df)
      success_rate = (
          round((success_runs / total_runs) * 100, 1) if total_runs > 0 else 0
      )
      avg_duration = (
          round(df["Duration_Sec"].mean(), 2)
          if "Duration_Sec" in df.columns
          else 0
      )

      c1, c2, c3, c4 = st.columns(4)
      c1.metric(
          "Pipeline Success Rate",
          f"{success_rate}%",
          f"{success_runs}/{total_runs} Passed",
      )
      c2.metric("Avg Latency", f"{avg_duration} sec")
      c3.metric("Total Records Logged", f"{len(df)}")
      if "Duration_Sec" in df.columns:
        c4.metric("Last Run Latency", f"{df['Duration_Sec'].iloc[-1]} sec")

      st.divider()
      price_cols = [
          col for col in success_df.columns if col.endswith("_USD")
      ]
      if price_cols:
        fig = px.line(
            success_df,
            x="Timestamp",
            y=price_cols,
            markers=True,
            title="Tracked Asset Price Trends Over Time",
            template="plotly_dark",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
      st.warning("No successful execution records found.")
  else:
    st.info("Click **'Execute Pipeline Now'** in the sidebar to begin.")

with tab2:
  st.subheader("📊 Output Dataset & Export Hub")
  if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    st.dataframe(df, use_container_width=True)

    if st.button("📥 Download CSV Report"):
      st.download_button(
          "Confirm Download",
          df.to_csv(index=False),
          file_name="report.csv",
          mime="text/csv",
      )
  else:
    st.info("Dataset is empty.")

with tab3:
  st.subheader("📜 Live Terminal Stream Logs")
  if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
      logs = f.read()
    st.text_area("Execution Stream Output", logs, height=420)
  else:
    st.info("No logs found.")

with tab4:
  st.markdown(
      "### ⚙️ Architecture\nSingle-file Streamlit Data Pipeline implementation"
      " ensuring zero module import errors."
  )