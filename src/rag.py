from typing import Dict, List, Optional
from openai import OpenAI
import logging
import tiktoken
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class RAGSystem:
    def __init__(self, vector_db) -> None:
        self.vector_db = vector_db
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.max_tokens = 8192  # Updated from 4096 to match GPT-3.5's actual limit
        self.max_response_tokens = 1000
        # Reduce context tokens to stay within limits
        self.max_context_tokens = 6000  # Leaving room for system message and response

    def truncate_content(self, content: str, max_tokens: int) -> str:
        tokens = self.tokenizer.encode(content)
        if len(tokens) <= max_tokens:
            return content
        return self.tokenizer.decode(tokens[:max_tokens])

    def generate_response_with_sources(self, query: str, max_context_docs: int = 3) -> Dict[str, any]:
        try:
            relevant_docs = self.vector_db.search(query, limit=max_context_docs)
            contexts_with_sources = []
            sources = []
            
            # Calculate tokens per document - reduce to stay within limits
            max_tokens_per_doc = self.max_context_tokens // (max_context_docs + 1)  # Add buffer

            for doc in relevant_docs:
                title = doc.get("title", "Untitled")
                content = doc.get("content", "")
                url = doc.get("url", "")
                
                # Truncate content if needed
                truncated_content = self.truncate_content(content, max_tokens_per_doc)
                
                contexts_with_sources.append(f"Source: {title}\nContent: {truncated_content}")
                sources.append({"title": title, "url": url})
            
            context = "\n\n".join(contexts_with_sources)
            prompt = self._create_prompt(query, context)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self._create_messages(prompt),
                temperature=0.5,
                max_tokens=self.max_response_tokens
            )
            
            return {
                "answer": response.choices[0].message.content,
                "sources": sources
            }
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": []
            }

    def _create_prompt(self, query: str, context: str) -> str:
        return f"""Based on the following sources, provide a comprehensive analysis of current trends and developments.
        
        Sources:
        {context}
        
        Question: What are the current trends and developments in: {query}
        
        Instructions:
        1. Focus on recent developments and current trends
        2. Highlight what's currently popular or gaining traction
        3. Include relevant statistics or data if available
        4. Organize trends from most significant to least
        5. Mention any emerging patterns or future predictions
        6. Cite specific sources for each trend
        7. Keep it concise and to the point
        8. Use markdown formatting
        9. Use bullet points when appropriate
        10. Use emojis when appropriate
        11. Provide Top 3 trends
        12. Every Point will have maxiumn of 20 Words with link below it.
        
        Answer:"""

    def _create_messages(self, prompt: str) -> List[Dict[str, str]]:
        return [
            {
                "role": "system",
                "content": "You are a research assistant that provides well-sourced information."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
