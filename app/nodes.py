from app.state import save_state
from app.tools import validate_email
from transformers import pipeline
from langchain.llms.base import LLM
from typing import Optional, List, Any, Dict
import time



class LocalFlanT5(LLM):
    # No class-level annotations → no Pydantic fields at all

    def __init__(self, model_name: str = "google/flan-t5-small", **kwargs):
        # ✅ Bypass Pydantic setattr guard during init
        object.__setattr__(self, "_pipeline", None)
        super().__init__(**kwargs)  # Call LLM.__init__ *after* setting _pipeline
        print(f"🧠 Loading {model_name}...")
        object.__setattr__(self, "_pipeline", pipeline(
            "text2text-generation",
            model=model_name,
            device=-1  # CPU
        ))
        print("✅ Model loaded.")

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        result = self._pipeline(
            f"Extract only the email: {prompt}",
            max_length=20,
            truncation=True,
            do_sample=False,
            num_beams=3,        # helps small models be more precise
            early_stopping=True
        )
        return result[0]["generated_text"].strip()

    @property
    def _llm_type(self) -> str:
        return "local-flan-t5"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": "google/flan-t5-small"}
#llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
# Instantiate once — reuse across nodes
llm = LocalFlanT5()  # uses flan-t5-small on CPU


def log_step(state, node_name: str, details: Any = None):
    entry = {
        "node": node_name,
        "timestamp": time.time(),
        "details": details or {}
    }
    state["execution_log"].append(entry)
    save_state(state)

# Node 1: LLM Interpretation
def interpret_input(state: dict) -> dict:
    # Flan-T5 is a text2text model → just pass a plain instruction-style prompt
    prompt = f"Extract only the email address from the following text. Respond with the email only, nothing else.\n\nText: {state['user_input']}"
    response = llm.invoke(prompt)  # or llm(prompt) — both work for LLM base
    extracted = response.strip()
    state["llm_response"] = extracted
    state["current_step"] = "validate"
    log_step(state, "interpret_input", {"extracted": extracted})
    return state

# Node 2: Tool Execution
def validate_email_tool(state: dict) -> dict:
    email = state["llm_response"]
    result = validate_email(email)
    state["tool_output"] = result["message"]
    state["current_step"] = "human_review"
    log_step(state, "validate_email_tool", result)
    return state

# Node 3: Human-in-the-Loop
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
            state["current_step"] = "interpret_input"  # retry
    else:
        # Treat input as corrected email
        state["llm_response"] = feedback
        state["tool_output"] = validate_email(feedback)["message"]
        state["approved"] = validate_email(feedback)["is_valid"]
        state["current_step"] = "end"
    
    log_step(state, "human_review", {"feedback": feedback, "approved": state["approved"]})
    return state

# Node 4: Final Output
def finalize(state: dict) -> dict:
    result = {
        "final_email": state["llm_response"],
        "status": "approved" if state["approved"] else "rejected",
        "attempts": state["attempts"]
    }
    print(f"\n✅ Final Result: {result}")
    log_step(state, "finalize", result)
    return state