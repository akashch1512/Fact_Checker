import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def query_gemini(claim: str, constraint: str = "verdict_and_short_reason") -> str:
    """
    Query Gemini AI to fact-check a claim with constraints.

    Args:
        claim (str): The statement to be fact-checked.
        constraint (str): One of:
            - "only_true": Only reply 'True' if the statement is factual; otherwise say nothing.
            - "only_false": Only reply 'False' if not factual; otherwise say nothing.
            - "verdict_and_short_reason" (default): Reply 'True' or 'False' and give a brief justification.

    Returns:
        str: The AI's response.
    """
    if constraint == "only_true":
        prompt = (
            f"Fact-check this statement: '{claim}'. "
            "Respond only with 'True' if the statement is correct. "
            "Say nothing if false. No explanation."
        )
    elif constraint == "only_false":
        prompt = (
            f"Fact-check this statement: '{claim}'. "
            "Respond only with 'False' if the statement is NOT correct. "
            "Say nothing if true. No explanation."
        )
    else:
        prompt = (
            f"Fact-check this statement: '{claim}'. "
            "Reply with 'True' or 'False' at the start and give a one-sentence reason (max 15 words)."
        )

    genai.configure(api_key=r"AIzaSyDVW4vPFJ7frbYhklDgKoaE9-3CEka5Hpg")
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    try:
        response = model.generate_content(prompt)
        return response.text if response.text else "No response."
    except Exception as e:
        return f"Error: {e}"
