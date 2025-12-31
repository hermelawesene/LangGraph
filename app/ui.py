from .graph import create_workflow
from .state import load_state

def run_cli():
    print("📧 Email Extraction & Validation Workflow")
    user_input = input("Enter your message: ")
    
    state = load_state()
    state["user_input"] = user_input
    state["attempts"] = 0
    state["approved"] = False

    app = create_workflow()
    final_state = app.invoke(state)
    
    print("\n📊 Execution Log:")
    for log in final_state["execution_log"]:
        print(f"  - {log['node']} @ {log['timestamp']}: {log['details']}")