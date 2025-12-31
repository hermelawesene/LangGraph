from transformers import pipeline
from langchain.llms.base import LLM
from pydantic import PrivateAttr  # ← critical import
from typing import Optional, List, Any, Dict


class LocalFlanT5(LLM):
    # Declare pipeline as a *private* attribute → Pydantic allows setattr in __init__
    _pipeline: Any = PrivateAttr()  # type is inferred; no need to annotate fully

    def __init__(self, model_name: str = "google/flan-t5-small", **kwargs):
        super().__init__(**kwargs)
        print(f"🧠 Loading {model_name}...")
        # Assign using private attr syntax
        self._pipeline = pipeline(
            "text2text-generation",
            model=model_name,
            device=-1  # CPU
        )
        print("✅ Model loaded.")

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        result = self._pipeline(
            f"Extract only the email: {prompt}",
            max_length=50,
            truncation=True,
            do_sample=False
        )
        return result[0]["generated_text"].strip()

    @property
    def _llm_type(self) -> str:
        return "local-flan-t5"

    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": "google/flan-t5-small"}

#llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
# Instantiate once — reuse across nodes
llm = LocalFlanT5()  # uses flan-t5-small on CPU

# test_llm.py
from pydantic.v1 import PrivateAttr
from typing import Any

class Test(LLM):
    _x: Any = PrivateAttr()
    def __init__(self): 
        super().__init__(); self._x = 42
    def _call(self, *a): return ""
    @property
    def _llm_type(self): return "test"

t = Test()  # ← should NOT crash
print("✅ Success")