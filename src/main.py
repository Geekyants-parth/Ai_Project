from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import traceback
import uuid
from .utils.logger import logger

from .crawler import WebCrawler
from .database import VectorDatabase
from .rag import RAGSystem

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="RAG API", description="API for RAG-based search and answers")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Incoming request", extra={
        'request_id': request_id,
        'method': request.method,
        'url': str(request.url),
        'headers': dict(request.headers)
    })
    
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(
            "Request failed",
            extra={
                'request_id': request_id,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        )
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "request_id": request_id}
        )

@app.post("/search", response_model=SearchResponse)
async def search_and_answer(request: SearchRequest, req: Request):
    request_id = req.state.request_id
    try:
        logger.info(
            f"Processing search request",
            extra={
                'request_id': request_id,
                'query': request.query
            }
        )
        
        # Check database
        existing_docs = vector_db.search(request.query, limit=request.num_results)
        
        if existing_docs and len(existing_docs) > 0:
            logger.info(
                "Found documents in cache",
                extra={
                    'request_id': request_id,
                    'doc_count': len(existing_docs)
                }
            )
            response = rag_system.generate_response_with_sources(request.query)
            return {
                "answer": response["answer"],
                "sources": response["sources"],
                "from_cache": True
            }
        
        # Crawl web
        logger.info(
            "Crawling web for documents",
            extra={'request_id': request_id}
        )
        documents = crawler.search_and_crawl(
            request.query,
            num_results=request.num_results
        )
        
        if not documents:
            logger.warning(
                "No documents found",
                extra={'request_id': request_id}
            )
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found"
            )
        
        # Store and generate response
        vector_db.add_documents(documents)
        response = rag_system.generate_response_with_sources(request.query)
        
        logger.info(
            "Successfully generated response",
            extra={
                'request_id': request_id,
                'source_count': len(response["sources"])
            }
        )
        
        return {
            "answer": response["answer"],
            "sources": response["sources"],
            "from_cache": False
        }
        
    except Exception as e:
        logger.error(
            "Error processing request",
            extra={
                'request_id': request_id,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

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

@app.get("/debug/logs")
async def get_recent_logs():
    """Endpoint to view recent logs (only in debug mode)"""
    if os.getenv("DEBUG") == "true":
        return {"logs": logger.get_recent_logs()}
    return {"message": "Debug mode not enabled"}

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check database connection
        db_status = vector_db.check_connection()
        # Check OpenAI API
        openai_status = rag_system.check_api()
        
        return {
            "status": "healthy" if db_status and openai_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "openai_api": "connected" if openai_status else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
