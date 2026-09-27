from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Filter, FieldCondition, MatchValue
from qdrant_client import models

from dotenv import load_dotenv
import os
from uuid import uuid4


load_dotenv()


# ===============================
# Qdrant Cloud connection
# ===============================

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)


COLLECTION_NAME = "documents"


# ===============================
# Create collection if needed
# ===============================

if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

client.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="document_id",
    field_schema=models.PayloadSchemaType.INTEGER
)


# ===============================
# Store chunks
# ===============================

def store_chunks(chunks, embeddings, filename, document_id):

    points = []

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):

        point = PointStruct(

            id=str(uuid4()),

            vector=embedding,

            payload={
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
                "text": chunk
            }
        )

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )


# ===============================
# Search chunks
# ===============================

def search_chunks(
    query_embedding,
    document_id,
    limit=3
):

    results = client.query_points(

        collection_name=COLLECTION_NAME,

        query=query_embedding,

        query_filter=Filter(

            must=[

                FieldCondition(

                    key="document_id",

                    match=MatchValue(
                        value=document_id
                    )
                )
            ]
        ),

        limit=limit
    )

    return results.points


# ===============================
# Delete document chunks
# ===============================

def delete_document_chunks(document_id):

    client.delete(

        collection_name=COLLECTION_NAME,

        points_selector=Filter(

            must=[

                FieldCondition(

                    key="document_id",

                    match=MatchValue(
                        value=document_id
                    )
                )
            ]
        )
    )