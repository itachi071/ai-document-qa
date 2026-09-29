    # from google import genai
    # from dotenv import load_dotenv
    # import os

    # load_dotenv()

    # client = genai.Client(
    #     api_key=os.getenv("GEMINI_API_KEY")
    # )

    # MODELS = [
    #     "gemini-3.8-flash",
    #     "gemini-3.7-flash",
    #     "gemini-3.6-flash",
    #     "gemini-3.5-flash",
    #     "gemini-2.5-flash"
    # ]


    # def generate_answer(question: str, context: str):

    #     prompt = f"""
    # You are a document question-answering assistant.

    # Answer the user's question using ONLY the provided document context.

    # Do not use outside knowledge.

    # If the answer cannot be found in the context, say:

    # "I could not find the answer in the provided document."

    # Document context:
    # {context}

    # Question:
    # {question}
    # """

    #     last_error = None

    #     for model in MODELS:

    #         try:
    #             print(f"Trying model: {model}")

    #             response = client.models.generate_content(
    #                 model=model,
    #                 contents=prompt
    #             )

    #             print(f"Success with model: {model}")

    #             return response.text

    #         except Exception as e:

    #             print(f"{model} failed: {e}")

    #             last_error = e

    #     raise Exception(
    #         f"All Gemini models failed. Last error: {last_error}"
    #     )


import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "openrouter/free"

URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_answer(question: str, context: str):

    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the provided document context.

Do not use outside knowledge.

If the answer cannot be found in the context, say:

"I could not find the answer in the provided document."

Document context:
{context}

Question:
{question}
"""

    try:

        print(f"Trying OpenRouter model: {MODEL}")

        response = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        answer = data["choices"][0]["message"]["content"]

        print(f"Success with OpenRouter model: {MODEL}")

        return answer

    except Exception as e:

        print(f"OpenRouter failed: {e}")

        raise Exception(
            f"OpenRouter failed: {e}"
        )

