"""
Cloud Cost Intelligence Agent — Streamlit UI

A conversational interface for interacting with the cost optimization agent.
Provides chat-based interaction, configuration sidebar, and visual
display of recommendations and agent reasoning steps.

Run: streamlit run app.py
"""

import streamlit as st
from datetime import datetime

from src.agent import create_cost_agent, run_analysis, AgentState
from src.memory import ConversationMemory
from langchain_core.messages import HumanMessage


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cloud Cost Intelligence Agent",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar — Configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image("https://img.shields.io/badge/☁️_Cloud_Cost-Intelligence_Agent-FF6B35?style=for-the-badge", width=280)
    st.markdown("---")

    st.header("⚙️ Configuration")

    account_id = st.text_input(
        "AWS Account ID",
        value="123456789012",
        help="The AWS account to analyze",
    )

    time_range = st.selectbox(
        "Analysis Period",
        options=[7, 14, 30, 60, 90],
        index=2,
        format_func=lambda x: f"Last {x} days",
    )

    model_choice = st.selectbox(
        "LLM Model",
        options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        index=0,
    )

    st.markdown("---")
    st.header("📊 Quick Actions")

    if st.button("🔍 Full Cost Analysis", use_container_width=True):
        st.session_state["trigger_analysis"] = True

    if st.button("💡 Find Quick Wins", use_container_width=True):
        st.session_state["trigger_quick_wins"] = True

    if st.button("📈 RI/SP Coverage Check", use_container_width=True):
        st.session_state["trigger_ri_check"] = True

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# ---------------------------------------------------------------------------
# Main Content Area
# ---------------------------------------------------------------------------

st.title("☁️ Cloud Cost Intelligence Agent")
st.caption("AI-powered FinOps optimization using LangGraph multi-step reasoning")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

# ---------------------------------------------------------------------------
# Chat Interface
# ---------------------------------------------------------------------------

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask about your cloud costs...")

if user_input or st.session_state.get("trigger_analysis"):
    # Clear trigger
    if st.session_state.get("trigger_analysis"):
        user_input = f"Run a full cost analysis for account {account_id} over the last {time_range} days"
        st.session_state["trigger_analysis"] = False

    # Display user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("🧠 Agent reasoning..."):
            # Show reasoning steps
            steps_container = st.container()

            with steps_container:
                st.markdown("**Agent Steps:**")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    step1 = st.empty()
                    step1.info("⏳ Analyzing costs...")
                with col2:
                    step2 = st.empty()
                    step2.markdown("⬜ Identify savings")
                with col3:
                    step3 = st.empty()
                    step3.markdown("⬜ Validate")
                with col4:
                    step4 = st.empty()
                    step4.markdown("⬜ Generate report")

            # Execute the analysis
            try:
                result = run_analysis(
                    account_id=account_id,
                    time_range_days=time_range,
                    model=model_choice,
                )
                st.session_state["analysis_result"] = result

                # Update step indicators
                step1.success("✅ Costs analyzed")
                step2.success("✅ Savings found")
                step3.success("✅ Validated")
                step4.success("✅ Report ready")

                # Display the report
                report = result.get("report", "Analysis complete.")
                st.markdown(report)

                # Store assistant response
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": report,
                })

            except Exception as e:
                st.error(f"Agent error: {str(e)}")
                st.info("Make sure your OPENAI_API_KEY is set in the .env file.")

# ---------------------------------------------------------------------------
# Metrics Dashboard (shown after analysis)
# ---------------------------------------------------------------------------

if st.session_state.get("analysis_result"):
    result = st.session_state["analysis_result"]

    st.markdown("---")
    st.subheader("📊 Analysis Metrics")

    col1, col2, col3, col4 = st.columns(4)

    total_spend = result.get("cost_data", {}).get("total_cost", 0)
    total_savings = result.get("total_savings", 0)
    rec_count = len(result.get("validated_recommendations", []))
    opt_score = result.get("optimization_score", 0)

    col1.metric("Monthly Spend", f"${total_spend:,.0f}")
    col2.metric("Potential Savings", f"${total_savings:,.0f}", delta=f"-{total_savings/total_spend*100:.1f}%" if total_spend else "0%")
    col3.metric("Recommendations", rec_count)
    col4.metric("Optimization Score", f"{opt_score}/100")

    # Service cost breakdown chart
    cost_data = result.get("cost_data", {})
    if cost_data.get("service_breakdown"):
        st.subheader("💸 Spend by Service")
        import pandas as pd

        df = pd.DataFrame(cost_data["service_breakdown"])
        st.bar_chart(df.set_index("service")["cost"])
