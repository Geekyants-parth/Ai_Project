import requests
import json

def test_search_api():
    url = "https://ai-project-dusky.vercel.app/search"
    
    # Test data
    payload = {
        "query": "What are the latest developments in AI?",
        "num_results": 5
    }
    
    # Make POST request
    response = requests.post(url, json=payload)
    
    # Print results
    print("\nStatus Code:", response.status_code)
    if response.status_code == 200:
        result = response.json()
        print("\n🤖 Answer:")
        print(result["answer"])
        print("\n📚 Sources:")
        for source in result["sources"]:
            print(f"- {source['title']}: {source['url']}")
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    test_search_api() 