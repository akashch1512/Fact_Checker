import os
from dotenv import load_dotenv
import requests

load_dotenv()

def query_perplexity(claim: str, constraint: str = "verdict_and_short_reason") -> str:
    """
    Query Perplexity AI to fact-check a claim with constraints.

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
            "Respond only with 'True' if the statement is correct. Do not explain. "
            "If not true, say nothing."
        )
    elif constraint == "only_false":
        prompt = (
            f"Fact-check this statement: '{claim}'. "
            "Respond only with 'False' if the statement is NOT correct. Do not explain. "
            "If not false, say nothing."
        )
    else:
        prompt = (
            f"Fact-check this statement: '{claim}'. "
            "Reply with 'True' or 'False' at the start followed by a very brief explanation "
            "of why the statement is or is not correct (max 15 words)."
        )

    url = "https://api.perplexity.ai/chat/completions"
    api_key = os.getenv("SONET_API_KEY")  # Or set in env
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
