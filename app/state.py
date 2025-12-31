from typing import TypedDict, List, Optional, Any
import json
import os

SESSION_FILE = "storage/session_state.json"

class WorkflowState(TypedDict):
    user_input: str
    current_step: str
    llm_response: Optional[str]
    tool_output: Optional[str]
    human_feedback: Optional[str]
    approved: bool
    attempts: int
    execution_log: List[dict]

def load_state() -> WorkflowState:
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            # Ensure list for log
            if "execution_log" not in data:
                data["execution_log"] = []
            return data
    return {
        "user_input": "",
        "current_step": "start",
        "llm_response": None,
        "tool_output": None,
        "human_feedback": None,
        "approved": False,
        "attempts": 0,
        "execution_log": []
    }

def save_state(state: WorkflowState):
    with open(SESSION_FILE, "w") as f:
        json.dump(state, f, indent=2)