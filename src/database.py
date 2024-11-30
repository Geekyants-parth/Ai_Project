import weaviate
import os
from dotenv import load_dotenv
from typing import List, Dict
import logging

load_dotenv()

class VectorDatabase:
    def __init__(self):
        self.client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL"),
            auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
            additional_headers={
                "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")
            }
        )
        self.setup_schema()

    def check_connection(self):
        try:
            if self.client.is_ready():
                logging.info("Successfully connected to Weaviate Cloud!")
                return True
            else:
                logging.error("Weaviate is not ready!")
                return False
        except Exception as e:
            logging.error(f"Error connecting to Weaviate: {str(e)}")
            return False

    def setup_schema(self):
        schema = {
            "class": "Document",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "url",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": True
                        }
                    }
                },
                {
                    "name": "title",
                    "dataType": ["string"],
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False
                        }
                    }
                }
            ]
        }

        try:
            # Check if schema exists
            existing_schema = self.client.schema.get()
            if any(class_obj["class"] == "Document" for class_obj in existing_schema["classes"]):
                logging.info("Schema already exists")
                return

            # Create schema
            self.client.schema.create_class(schema)
            logging.info("Schema created successfully")
        except Exception as e:
            logging.error(f"Error with schema: {str(e)}")
            raise

    def add_documents(self, documents: List[Dict[str, str]]):
        try:
            with self.client.batch as batch:
                for doc in documents:
                    batch.add_data_object(
                        data_object={
                            "content": doc["content"],
                            "url": doc["url"],
                            "title": doc["title"]
                        },
                        class_name="Document"
                    )
            logging.info(f"Successfully added {len(documents)} documents")
        except Exception as e:
            logging.error(f"Error adding documents: {str(e)}")

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        try:
            response = (
                self.client.query
                .get("Document", ["content", "url", "title"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            return response["data"]["Get"]["Document"]
        except Exception as e:
            logging.error(f"Error searching: {str(e)}")
            return []

    def view_stored_data(self):
        try:
            response = (
                self.client.query
                .get("Document", ["content", "url", "title"])
                .with_limit(100)  # Get first 10 documents
                .do()
            )
            
            documents = response["data"]["Get"]["Document"]
            print(f"\n📚 Found {len(documents)} documents in database:")
            for i, doc in enumerate(documents, 1):
                print(f"\n--- Document {i} ---")
                print(f"Title: {doc.get('title', 'No Title')}")
                print(f"URL: {doc.get('url', 'No URL')}")
                print(f"Content Preview: {doc.get('content', 'No Content')[:200]}...")
                print("-" * 50)
            
        except Exception as e:
            print(f"Error viewing data: {str(e)}")

    def clear_documents(self):
        """Clear all documents from the database"""
        try:
            self.client.batch.delete_objects(
                class_name="Document",
                where={"operator": "NotNull", "path": ["id"]}
            )
            logging.info("Successfully cleared all documents")
        except Exception as e:
            logging.error(f"Error clearing documents: {str(e)}")
            raise e
