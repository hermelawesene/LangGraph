import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY").strip().strip('"').strip("'")
if not api_key:
    raise ValueError("Missing GOOGLE_API_KEY in .env")

genai.configure(api_key=api_key)

# ✅ Use gemini-2.5-flash — confirmed available in your list
model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content(
    "Extract ONLY the email address. Return just the email. If none, return 'none'.\n\n"
    "Text: Hi, my email is user@example.com — please confirm."
)
print("✅ Response:", repr(response.text))