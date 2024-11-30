import os
from dotenv import load_dotenv
from src.crawler import WebCrawler
from src.database import VectorDatabase
from src.rag import RAGSystem
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

def initialize_system():
    print("🚀 Initializing RAG system...")
    db = VectorDatabase()
    rag = RAGSystem(db)
    crawler = WebCrawler()
    return db, rag, crawler

def search_crawl_and_answer(query: str, db: VectorDatabase, rag: RAGSystem, crawler: WebCrawler):
    try:
        # First, search in existing database
        print(f"🔍 Searching existing database for: {query}")
        existing_docs = db.search(query, limit=100)  # Get top 3 relevant documents
        
        # Check if we have relevant documents
        if existing_docs and len(existing_docs) > 0:
            print("📚 Found relevant information in database!")
            # Generate response from existing documents
            response = rag.generate_response_with_sources(query)
            return response
            
        # If no relevant documents found, perform web search and crawl
        print("🌐 No relevant information found in database. Searching the web...")
        documents = crawler.search_and_crawl(query, num_results=5)
        
        if not documents:
            return {"answer": "Sorry, I couldn't find relevant information for your query.", "sources": []}
        
        # Store the new documents
        print("💾 Storing new documents in database...")
        db.add_documents(documents)
        
        # Generate response
        print("🤔 Generating response...")
        response = rag.generate_response_with_sources(query)
        
        return response
        
    except Exception as e:
        logging.error(f"Error in search_crawl_and_answer: {str(e)}")
        return {"answer": f"An error occurred: {str(e)}", "sources": []}

def interactive_rag():
    db, rag, crawler = initialize_system()
    
    while True:
        print("\n" + "="*50)
        print("RAG Interactive Search System")
        print("="*50)
        print("1. Ask a question")
        print("2. View stored documents")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            query = input("\nEnter your question: ")
            response = search_crawl_and_answer(query, db, rag, crawler)
            
            print("\n🤖 Answer:")
            print(response["answer"])
            
            if response["sources"]:
                print("\n📚 Sources:")
                for source in response["sources"]:
                    print(f"- {source['title']}: {source['url']}")
        
        elif choice == "2":
            try:
                db.view_stored_data()
            except Exception as e:
                print(f"\n❌ Error viewing data: {str(e)}")
                
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    interactive_rag()