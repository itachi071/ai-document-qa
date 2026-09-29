# from google import genai
# from dotenv import load_dotenv
# import os

# load_dotenv()

# client = genai.Client(
#     api_key=os.getenv("GEMINI_API_KEY")
# )


# def create_embedding(text):
#     response = client.models.embed_content(
#         model="gemini-embedding-001",
#         contents=text,
#         config={
#             "output_dimensionality": 768
#         }
#     )

#     return response.embeddings[0].values


import os
import requests
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")

JINA_URL = "https://api.jina.ai/v1/embeddings"

BATCH_SIZE = 100


def create_embedding(text):

    response = requests.post(
        JINA_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JINA_API_KEY}"
        },
        json={
            "model": "jina-embeddings-v2-base-en",
            "input": [text]
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["data"][0]["embedding"]


def create_embeddings(chunks):

    all_embeddings = []

    for start in range(0, len(chunks), BATCH_SIZE):

        batch = chunks[start:start + BATCH_SIZE]

        print(
            f"Embedding chunks {start} to "
            f"{start + len(batch) - 1}"
        )

        response = requests.post(
            JINA_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {JINA_API_KEY}"
            },
            json={
                "model": "jina-embeddings-v2-base-en",
                "input": batch
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        batch_embeddings = [
            item["embedding"]
            for item in data["data"]
        ]

        all_embeddings.extend(batch_embeddings)

    print(f"Total embeddings created: {len(all_embeddings)}")

    return all_embeddings