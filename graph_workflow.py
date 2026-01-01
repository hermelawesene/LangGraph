# graph_workflow.py
from app.graph import create_workflow

app = create_workflow()

try:
    # ✅ Correct for LangGraph >= 0.1.4
    app.get_graph().draw_mermaid_png(output_file_path="workflow.png")
    print("✅ Graph saved as 'workflow.png'")
except Exception as e:
    print(f"⚠️ PNG export failed: {e}")
    
    # Fallback: Mermaid source
    try:
        mermaid_code = app.get_graph().draw_mermaid()
        with open("workflow.mmd", "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        print("📁 Mermaid code saved as 'workflow.mmd'")
        print("🌐 Paste into https://mermaid.live → Export PNG")
    except Exception as e2:
        print(f"❌ All export methods failed: {e2}")