import re

def validate_email(email: str) -> dict:
    is_valid = bool(re.match(r"[^@]+@[^<EMAIL>]+\.[^@]+", email))
    return {
        "is_valid": is_valid,
        "message": "Valid email" if is_valid else "Invalid email format"
    }