from database import VectorDatabase
import logging

logging.basicConfig(level=logging.INFO)

def test_weaviate_connection():
    try:
        db = VectorDatabase()
        if db.check_connection():
            print("✅ Successfully connected to Weaviate Cloud!")
        else:
            print("❌ Failed to connect to Weaviate")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_weaviate_connection() 