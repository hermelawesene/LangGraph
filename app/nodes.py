# app/nodes.py
import time
import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.llms.base import LLM
from pydantic.v1 import PrivateAttr
from typing import Any, Optional, List, Dict

from app.state import save_state
from app.tools import validate_email

load_dotenv()

#  Ensure GOOGLE_API_KEY is set
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError(" GOOGLE_API_KEY not found in .env")

#  Fully compliant LLM wrapper for LangChain
class GeminiProLLM(LLM):
    _model: Any = PrivateAttr()

    def __init__(self, model_name: str = "gemini-2.5-flash", **kwargs):
        super().__init__(**kwargs)
        api_key = os.getenv("GOOGLE_API_KEY").strip().strip('"').strip("'")
        genai.configure(api_key=api_key)
        object.__setattr__(self, "_model", genai.GenerativeModel(model_name))
        print(f" Gemini LLM ready: {model_name}")

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        full_prompt = (
            "Extract ONLY the email address. Return just the email. If none, return 'none'.\n\n"
            f"Text: {prompt}"
        )
        try:
            response = self._model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            print(f" LLM error: {e}")
            return "none"

    #  REQUIRED: abstract method — must be @property
    @property
    def _llm_type(self) -> str:
        return "gemini"

    #  REQUIRED for LangChain serialization
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": "gemini-2.5-flash"}


#  Instantiate once — global singleton
llm = GeminiProLLM()


# ======== Workflow Nodes ========
def log_step(state, node_name: str, details: Any = None):
    entry = {
        "node": node_name,
        "timestamp": time.time(),
        "details": details or {}
    }
    state["execution_log"].append(entry)
    save_state(state)


def interpret_input(state: dict) -> dict:
    prompt = (
        "Extract ONLY the email address. Return just the email. If none, 'none'.\n\n"
        f"Text: {state['user_input']}"
    )
    response = llm.invoke(prompt)
    extracted = response.strip()
    state["llm_response"] = extracted
    state["current_step"] = "validate"
    log_step(state, "interpret_input", {"extracted": extracted})
    return state


def validate_email_tool(state: dict) -> dict:
    email = state["llm_response"]
    result = validate_email(email)
    state["tool_output"] = result["message"]
    state["current_step"] = "human_review"
    log_step(state, "validate_email_tool", result)
    return state


def request_human_feedback(state: dict) -> dict:
    print(f"\n[🔄 Human Review Required]")
    print(f"Extracted email: {state['llm_response']}")
    print(f"Validation result: {state['tool_output']}")
    feedback = input("Approve? (y/n) or enter corrected email: ").strip()

    if feedback.lower() == 'y':
        state["approved"] = True
        state["current_step"] = "end"
    elif feedback.lower() == 'n':
        state["approved"] = False
        state["attempts"] += 1
        if state["attempts"] >= 2:
            state["current_step"] = "end"
        else:
            state["current_step"] = "interpret_input"
    else:
        # Treat input as corrected email
        state["llm_response"] = feedback
        validation = validate_email(feedback)
        state["tool_output"] = validation["message"]
        state["approved"] = validation["is_valid"]
        state["current_step"] = "end"

    log_step(state, "human_review", {
        "feedback": feedback,
        "approved": state["approved"]
    })
    return state

# def request_human_feedback(state: dict) -> dict:
#     state["current_step"] = "human_review"
#     state["waiting_for_human"] = True

#     log_step(state, "human_review_requested", {
#         "email": state.get("llm_response"),
#         "validation": state.get("tool_output"),
#     })

#     # 🔹 IMPORTANT: Do NOT loop or ask for input here
#     return state


def finalize(state: dict) -> dict:
    result = {
        "final_email": state["llm_response"],
        "status": "approved" if state["approved"] else "rejected",
        "attempts": state["attempts"]
    }
    print(f"\n Final Result: {result}")
    log_step(state, "finalize", result)
    return state