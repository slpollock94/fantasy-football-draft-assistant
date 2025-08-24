import os
import openai
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def get_openai_api_key():
    # Try to load from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Try to load from .env file if not already loaded
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment or .env file.")
    return api_key


def parse_table_with_openai(text: str, columns: List[str]) -> List[Dict[str, str]]:
    """
    Use OpenAI to parse a block of text into a list of dicts with the given columns.
    Compatible with openai>=1.0.0 client interface.
    """
    api_key = get_openai_api_key()
    prompt = (
        f"Extract the following fantasy football rankings into a JSON array of objects with columns: {', '.join(columns)}. "
        "If a value is missing, use an empty string. Data:\n" + text
    )
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0
        )
    except (openai.APIError, openai.APIConnectionError, openai.APITimeoutError) as e:
        logger.exception(
            "OpenAI API request failed", extra={"error_type": e.__class__.__name__}
        )
        raise

    if not getattr(response, "choices", None):
        logger.error(
            "OpenAI response missing choices", extra={"response": str(response)}
        )
        raise ValueError("OpenAI response missing choices")

    choice = response.choices[0]
    if not getattr(choice, "message", None) or not getattr(choice.message, "content", None):
        logger.error(
            "OpenAI response missing message content", extra={"response": str(response)}
        )
        raise ValueError("OpenAI response missing message content")

    content = choice.message.content

    import json
    import re
    try:
        # Remove markdown code block markers if present
        content = content.strip()
        if content.startswith('```json'):
            content = content[len('```json'):].strip()
        if content.startswith('```'):
            content = content[len('```'):].strip()
        if content.endswith('```'):
            content = content[:-3].strip()
        # Now extract JSON array
        start = content.find('[')
        end = content.rfind(']') + 1
        json_str = content[start:end]
        return json.loads(json_str)
    except Exception:
        logger.exception(
            "Failed to parse OpenAI response", extra={"response_content": content}
        )
        raise ValueError(
            f"Could not parse OpenAI response as JSON.\nResponse: {content}"
        )
