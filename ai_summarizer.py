
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def summarize_news(title, description=""):

    if not API_KEY:
        return "Error: GEMINI_API_KEY is missing from .env."

    title = str(title or "").strip()
    description = str(description or "").strip()

    if not title and not description:
        return "No news content available to summarize."

    prompt = f"""
    Summarize this news in 2-4 simple bullet points.
    Use only the information provided. Do not invent facts.

    Headline: {title}
    Description: {description or "Not available"}
    """

    try:
        client = genai.Client(api_key=API_KEY)

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        if response.text:
            return response.text.strip()

        return "No summary returned. Please try again."

    except Exception as exc:
        print("Gemini API Error:", repr(exc))
        return f"AI summary failed: {exc}"