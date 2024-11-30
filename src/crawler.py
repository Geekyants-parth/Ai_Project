from googlesearch import search
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import os
from urllib.parse import urljoin
import time

class WebCrawler:
    def __init__(self):
        self.visited_urls = set()

    def get_page_content(self, url: str) -> Dict[str, str]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            # Get title
            title = soup.title.string if soup.title else "No Title"
            
            # Get main content
            paragraphs = soup.find_all('p')
            content = ' '.join(p.get_text().strip() for p in paragraphs)
            
            # Clean up text
            content = ' '.join(content.split())
            
            return {
                "title": title,
                "content": content,
                "url": url
            }
        except Exception as e:
            logging.error(f"Error crawling {url}: {str(e)}")
            return None

    def search_and_crawl(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        documents = []
        logging.info(f"🔍 Searching Google for: {query}")
        
        try:
            # Get search results
            search_results = search(query, num_results=num_results)
            
            for url in search_results:
                if url in self.visited_urls:
                    continue
                
                logging.info(f"Crawling: {url}")
                document = self.get_page_content(url)
                
                if document and len(document["content"]) > 100:  # Ensure we have meaningful content
                    documents.append(document)
                    self.visited_urls.add(url)
                
                # Be nice to servers
                time.sleep(1)
                
                if len(documents) >= num_results:
                    break
            
            logging.info(f"✅ Crawled {len(documents)} pages")
            return documents
            
        except Exception as e:
            logging.error(f"Error in search and crawl: {str(e)}")
            return documents
