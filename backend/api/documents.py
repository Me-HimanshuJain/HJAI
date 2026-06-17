from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List
import uuid
from database.database import get_db
from sqlalchemy.orm import Session
from rag.document_parser import DocumentParser
from rag.chunker import TextChunker
from memory.embeddings import EmbeddingService
from memory.chroma_client import ChromaService
from pydantic import BaseModel
from services.llm_service import LLMService

router = APIRouter()
DOC_COLLECTION = "user_documents"

@router.post("/upload")
async def upload_document(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Read file bytes
    file_bytes = await file.read()
    filename = file.filename.lower()
    
    # 1. Parse Document
    text = ""
    if filename.endswith(".pdf"):
        text = DocumentParser.parse_pdf(file_bytes)
    elif filename.endswith(".docx"):
        text = DocumentParser.parse_docx(file_bytes)
    elif filename.endswith(".txt"):
        text = DocumentParser.parse_txt(file_bytes)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format.")
        
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from document.")
        
    # 2. Chunk Text
    chunks = TextChunker.chunk_text(text)
    
    # 3. Generate Embeddings
    embeddings = EmbeddingService.generate_embeddings(chunks)
    
    # 4. Store in ChromaDB
    document_id = str(uuid.uuid4())
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"user_id": user_id, "document_id": document_id, "filename": filename, "chunk_index": i} for i in range(len(chunks))]
    
    ChromaService.add_documents(
        collection_name=DOC_COLLECTION,
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    # In a real app, also save to Postgres 'documents' and 'document_chunks' tables here.
    return {"status": "success", "document_id": document_id, "chunks_processed": len(chunks)}


class DocumentChatRequest(BaseModel):
    user_id: str
    document_id: str
    question: str

@router.post("/chat")
async def chat_with_document(request: DocumentChatRequest):
    # 1. Embed the question
    query_embedding = EmbeddingService.generate_embedding(request.question)
    
    # 2. Search Vector DB
    results = ChromaService.query_collection(
        collection_name=DOC_COLLECTION,
        query_embeddings=[query_embedding],
        n_results=5
    )
    
    # Filter by user_id and document_id
    relevant_chunks = []
    if results and results.get("documents") and results.get("metadatas"):
        for i, docs in enumerate(results["documents"]):
            metas = results["metadatas"][i]
            for j, doc in enumerate(docs):
                meta = metas[j]
                if meta.get("user_id") == request.user_id and meta.get("document_id") == request.document_id:
                    relevant_chunks.append(doc)
                    
    if not relevant_chunks:
        return {"response": "I could not find any relevant information in the document to answer your question."}
        
    # 3. Construct Context and Prompt
    context = "\n\n".join(relevant_chunks)
    system_prompt = f"You are a document analysis assistant. Answer the user's question based ONLY on the following context:\n\n{context}"
    
    # 4. Generate Response
    response = await LLMService.generate_response(prompt=request.question, system=system_prompt)
    
    return {"response": response}
