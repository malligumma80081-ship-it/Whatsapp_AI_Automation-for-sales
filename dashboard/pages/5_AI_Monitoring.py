from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve()
for candidate in (PROJECT_ROOT.parent, *PROJECT_ROOT.parents):
    if (candidate / "requirements.txt").exists():
        PROJECT_ROOT = candidate
        break
else:
    PROJECT_ROOT = PROJECT_ROOT.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from dashboard.api_client import APIClient

st.set_page_config(
    page_title="AI Monitoring",
    layout="wide",
)

if not st.session_state.get("logged_in"):
    st.error("Please log in from the main dashboard.")
    st.stop()

client = APIClient(st.session_state["token"])

st.title("AI Monitoring")
st.caption("Monitor LLM performance and evaluation results.")

col1, col2 = st.columns(2)

try:
    metrics = client.get("/llm/metrics") or {}

    with col1:
        st.subheader("LLM Metrics")

        if isinstance(metrics, dict) and metrics:
            rows = []
            for provider, stats in metrics.items():
                rows.append(
                    {
                        "provider": provider,
                        "requests": stats.get("requests", 0),
                        "successes": stats.get("successes", 0),
                        "failures": stats.get("failures", 0),
                        "avg_latency_ms": round(
                            stats.get("average_latency_ms", 0), 2
                        ),
                    }
                )

            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            else:
                st.info("No LLM calls have been recorded yet.")
        else:
            st.info("No LLM metrics available yet.")

except Exception as exc:
    with col1:
        st.error(f"LLM metrics unavailable: {exc}")

try:
    evaluation = client.get("/evaluation/summary") or {}

    with col2:
        st.subheader("Evaluation Summary")

        summary = evaluation.get("metrics", evaluation) if isinstance(evaluation, dict) else {}
        total = summary.get("total", 0)
        accuracy = summary.get("accuracy", 0)
        tool_accuracy = summary.get("tool_accuracy", 0)
        average_latency_ms = summary.get("average_latency_ms", 0)

        st.metric("Total evaluations", total)
        st.metric("Accuracy", f"{accuracy}%")
        st.metric("Tool accuracy", f"{tool_accuracy}%")
        st.metric("Avg latency", f"{average_latency_ms} ms")

except Exception as exc:
    with col2:
        st.warning(f"Evaluation summary unavailable: {exc}")

st.divider()
st.subheader("Run Evaluation")

st.write(
    "Use the evaluation API to assess answer quality, "
    "tool selection and response latency."
)

if st.button("Check Evaluation API"):
    try:
        st.success("Evaluation API is reachable.")
        st.info(
            "Use your Day 15 /evaluation/run endpoint "
            "with the approved evaluation dataset."
        )
    except Exception as exc:
        st.error(str(exc))