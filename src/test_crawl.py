import os
from dotenv import load_dotenv
from crawler import WebCrawler
from database import VectorDatabase
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()

def test_crawl_and_store():
    try:
        # Initialize crawler and database
        crawler = WebCrawler(os.getenv("CRAWL_WEBSITE"))
        db = VectorDatabase()

        # Check database connection
        if not db.check_connection():
            print("❌ Failed to connect to database")
            return

        # Crawl website
        print(f"🕷️ Crawling {os.getenv('CRAWL_WEBSITE')}...")
        documents = crawler.crawl(max_pages=5)  # Limit to 5 pages for testing
        print(f"✅ Crawled {len(documents)} pages")

        # Store in database
        print("💾 Storing documents in Weaviate...")
        db.add_documents(documents)
        print("✅ Documents stored successfully")

        # Test search
        print("\n🔍 Testing search...")
        test_query = "What are Shah Rukh Khan's most famous movies?"
        results = db.search(test_query, limit=2)
        
        print("\nSearch Results:")
        for result in results:
            print(f"\nTitle: {result.get('title', 'No Title')}")
            print(f"Content: {result.get('content', '')[:200]}...")
            print(f"URL: {result.get('url', '')}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_crawl_and_store() 