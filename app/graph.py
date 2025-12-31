from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .nodes import interpret_input, validate_email_tool, request_human_feedback, finalize

def create_workflow():
    workflow = StateGraph(WorkflowState)

    workflow.add_node("interpret_input", interpret_preprocess:=lambda s: interpret_input(s))
    workflow.add_node("validate", validate_email_tool)
    workflow.add_node("human_review", request_human_feedback)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("interpret_input")

    # Conditional edges
    def route_after_interpret(state):
        return "validate"

    def route_after_validate(state):
        return "human_review"

    def route_after_human(state):
        if state["approved"] or state["attempts"] >= 2:
            return "finalize"
        else:
            return "interpret_input"  # loop back

    workflow.add_edge("interpret_input", "validate")
    workflow.add_edge("validate", "human_review")
    workflow.add_conditional_edges("human_review", route_after_human)
    workflow.add_edge("finalize", END)

    return workflow.compile()