from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import logging

from .crawler import WebCrawler
from .database import VectorDatabase
from .rag import RAGSystem

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="RAG API", description="API for RAG-based search and answers")

# Initialize components
vector_db = VectorDatabase()
rag_system = RAGSystem(vector_db)
crawler = WebCrawler()

class SearchRequest(BaseModel):
    query: str
    num_results: Optional[int] = 5

class SearchResponse(BaseModel):
    answer: str
    sources: List[dict]
    from_cache: bool = False  # To indicate if response came from database

@app.post("/search", response_model=SearchResponse)
async def search_and_answer(request: SearchRequest):
    """
    Search, crawl, and answer questions using RAG
    First checks database, then crawls if needed
    """
    try:
        # First check database
        logging.info(f"Searching database for: {request.query}")
        existing_docs = vector_db.search(request.query, limit=request.num_results)
        
        if existing_docs and len(existing_docs) > 0:
            logging.info("Found relevant documents in database")
            response = rag_system.generate_response_with_sources(request.query)
            return {
                "answer": response["answer"],
                "sources": response["sources"],
                "from_cache": True
            }
        
        # If no relevant docs found, crawl the web
        logging.info("No relevant documents found in database, crawling web...")
        documents = crawler.search_and_crawl(request.query, num_results=request.num_results)
        
        if not documents:
            raise HTTPException(status_code=404, detail="No relevant documents found")
        
        # Store new documents
        vector_db.add_documents(documents)
        
        # Generate response
        response = rag_system.generate_response_with_sources(request.query)
        
        return {
            "answer": response["answer"],
            "sources": response["sources"],
            "from_cache": False
        }
    except Exception as e:
        logging.error(f"Error in search_and_answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_stored_documents():
    """
    Get all stored documents from the vector database
    """
    try:
        documents = vector_db.get_all_documents(limit=100)
        if not documents:
            return {"documents": []}
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
async def clear_documents():
    """
    Clear all stored documents from the vector database
    """
    try:
        vector_db.clear_documents()
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Welcome page
    """
    return {
        "message": "Welcome to RAG API",
        "version": "1.0",
        "endpoints": {
            "/search": "POST - Search and get answers (checks database first)",
            "/documents": "GET - View stored documents",
            "/documents": "DELETE - Clear stored documents",
            "/": "GET - This welcome page"
        }
    }
