# app_streamlit.py
import streamlit as st
import time
from app.graph import create_workflow
from app.state import load_state, save_state

# Initialize
st.set_page_config(page_title="📧 Email Extractor", layout="wide")
st.title("📧 AI + Human Email Extraction Workflow")

# Load or initialize state
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = load_state()
if "app" not in st.session_state:
    st.session_state.app = create_workflow()

state = st.session_state.workflow_state
app = st.session_state.app

# === UI: User Input ===
st.subheader("📝 Enter Message")
user_input = st.text_input(
    "Type a message containing an email:",
    placeholder="e.g., 'Hi, my email is user@example.com — please confirm.'",
    key="user_input"
)

if st.button("🚀 Start Extraction", type="primary") and user_input:
    # Update state
    state["user_input"] = user_input
    state["attempts"] = 0
    state["execution_log"] = []  # reset log
    save_state(state)
    
    # Run workflow
    with st.spinner("Running AI workflow..."):
        final_state = app.invoke(state)
    
    # Update session state
    st.session_state.workflow_state = final_state
    st.rerun()

# === UI: Current Status ===
if state["user_input"]:
    st.divider()
    st.subheader("🔍 Current Status")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Step", state.get("current_step", "start"))
    col2.metric("Attempts", state.get("attempts", 0))
    col3.metric("Approved?", "✅ Yes" if state.get("approved") else "❌ No")

    # Show LLM & Tool Output
    if state.get("llm_response"):
        st.info(f"🤖 LLM Extracted: `{state['llm_response']}`")
    if state.get("tool_output"):
        st.warning(f"🔧 Validation: {state['tool_output']}")

    # === UI: Human Review (only if needed) ===
    if state.get("current_step") == "human_review":
        st.divider()
        st.subheader("🔄 Human Review Required")
        
        feedback = st.text_input(
            "Approve (y), Reject (n), or Enter Corrected Email:",
            key="feedback_input"
        )
        
        if st.button("✅ Submit"):
            # Simulate human_review node logic
            if feedback.lower() == 'y':
                state["approved"] = True
                state["current_step"] = "finalize" 
            elif feedback.lower() == 'n':
                state["approved"] = False
                state["attempts"] += 1
                if state["attempts"] >= 2:
                    state["current_step"] = "finalize"
                else:
                    state["current_step"] = "interpret_input"
            else:
                # Treat as corrected email
                state["llm_response"] = feedback
                from app.tools import validate_email
                result = validate_email(feedback)
                state["tool_output"] = result["message"]
                state["approved"] = result["is_valid"]
                state["current_step"] = "finalize"
            
            # Save & re-run workflow from current step
            save_state(state)
            with st.spinner("Processing..."):
                if state["current_step"] == "interpret_input":
                    # Re-run from interpret_input
                    final_state = app.invoke(state)
                    st.session_state.workflow_state = final_state
                else:
                    # Go directly to finalize
                    from app.nodes import finalize
                    final_state = finalize(state)
                    st.session_state.workflow_state = final_state
            st.rerun()

    # === UI: Final Result ===
    if state.get("current_step") == "end" or state.get("final_email"):
        st.divider()
        st.subheader("✅ Final Result")
        result = {
            "final_email": state.get("llm_response", "N/A"),
            "status": "approved" if state.get("approved") else "rejected",
            "attempts": state.get("attempts", 0)
        }
        st.success(f"**Email**: `{result['final_email']}`")
        st.json(result)

# === UI: Execution Log ===
if state.get("execution_log"):
    st.divider()
    st.subheader("📜 Execution Log")
    for i, entry in enumerate(reversed(state["execution_log"])):  # newest first
        with st.expander(f"🔹 {entry['node']} @ {time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))}", expanded=i==0):
            st.write(f"**Node**: `{entry['node']}`")
            st.write(f"**Timestamp**: `{entry['timestamp']:.3f}`")
            st.json(entry["details"])

# === Reset Button ===
if st.button("🔄 Reset Workflow"):
    st.session_state.workflow_state = load_state()
    st.rerun()