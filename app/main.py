from fastapi import FastAPI, Depends, HTTPException
import os

from fastapi import UploadFile, File
from pypdf import PdfReader
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, get_db
from .models import Base, Document
from .schemas import DocumentCreate
from .chunker import split_text
from .embedings import  create_embeddings, create_embedding
from .vector_db import store_chunks, delete_document_chunks
from .schemas import QuestionRequest
from .vector_db import search_chunks
from .llm import generate_answer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "AI Document Q&A API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents")
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    new_document = Document(
        title=document.title,
        description=document.description,
        author=document.author
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document

@app.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()

    return documents

@app.get("/documents/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):

    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Delete chunks from Qdrant
    delete_document_chunks(document_id)

    # Delete uploaded PDF
    if document.filename:

        file_path = os.path.join(
            "uploads",
            document.filename
        )

        if os.path.exists(file_path):
            os.remove(file_path)

    # Delete document from PostgreSQL
    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    os.makedirs("uploads", exist_ok=True)
    
    file_path = os.path.join(
        "uploads",
        file.filename
    )

    contents = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    # Create document in PostgreSQL

    new_document = Document(
        title=file.filename,
        description="Uploaded PDF document",
        author="Aakash",
        filename=file.filename
    )

    db.add(new_document)

    db.commit()

    db.refresh(new_document)

    # Get PostgreSQL document ID

    document_id = new_document.id

    # Split text

    chunks = split_text(text)

    # Create embeddings

    embeddings = create_embeddings(chunks)
    # Store chunks in Qdrant

    store_chunks(
        chunks,
        embeddings,
        file.filename,
        document_id
    )

    return {
        "message": "Document uploaded successfully",
        "document_id": document_id,
        "filename": file.filename,
        "pages": len(reader.pages),
        "total_chunks": len(chunks)
    }

# @app.post("/ask")
# def ask_question(request: QuestionRequest):

#     # 1. Convert question into embedding
#     query_embedding = create_embedding(request.question)

#     # 2. Search Qdrant
#     results = search_chunks(query_embedding)

#     # 3. Build context from retrieved chunks
#     context = ""

#     for result in results:
#         context += result.payload["text"] + "\n\n"

#     # 4. Ask Gemini
#     answer = generate_answer(
#         request.question,
#         context
#     )

#     # 5. Return answer + sources
#     return {
#         "question": request.question,
#         "answer": answer,
#         "sources": [
#             {
#                 "filename": result.payload["filename"],
#                 "chunk_index": result.payload["chunk_index"],
#                 "score": result.score
#             }
#             for result in results
#         ]
#     }

@app.post("/documents/{document_id}/ask")
def ask_document_question(
    document_id: int,
    request: QuestionRequest,
    db: Session = Depends(get_db)
):

    # Check that document exists in PostgreSQL

    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Create question embedding

    query_embedding = create_embedding(
        request.question
    )

    # Search only this document's chunks

    results = search_chunks(
        query_embedding,
        document_id
    )

    # Build context

    context = ""

    for result in results:
        context += result.payload["text"] + "\n\n"

    # Generate answer

    answer = generate_answer(
        request.question,
        context
    )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "question": request.question,
        "answer": answer,
        "sources": [
            {
                "chunk_index": result.payload["chunk_index"],
                "score": result.score
            }
            for result in results
        ]
    }
