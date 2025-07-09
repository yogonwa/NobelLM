import requests
import json

# Test the new HTTP endpoint
url = "https://yogonwa--nobel-embedder-clean-slate-embed-query.modal.run"
api_key = "6dab23095a3f8968074d7c9152d6707f3f7445bc145022f46fcceb0712864147"

# Test query
query = "What did Toni Morrison say about justice?"

# Make the HTTP request
headers = {
    "Content-Type": "application/json"
}

data = {
    "api_key": api_key,
    "text": query
}

print(f"Testing HTTP endpoint: {url}")
print(f"Query: '{query}'")
print(f"Headers: {headers}")
print(f"Data: {data}")
print("-" * 50)

# Test POST to the endpoint
print(f"Testing POST to endpoint: {url}")

try:
    response = requests.post(url, json=data, headers=headers, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        result = response.json()
        embedding = result["embedding"]
        print(f"✅ Success!")
        print(f"Embedding length: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        print(f"Last 5 values: {embedding[-5:]}")
        
        # Check if embedding is normalized (values should be between -1 and 1)
        max_val = max(abs(x) for x in embedding)
        min_val = min(embedding)
        max_abs = max(abs(x) for x in embedding)
        print(f"Embedding range: [{min_val:.4f}, {max(embedding):.4f}]")
        print(f"Max absolute value: {max_abs:.4f}")
        
        if max_abs <= 1.0:
            print("✅ Embedding appears to be normalized")
        else:
            print("⚠️  Embedding may not be normalized")
            
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response body: {response.text}")
        
except Exception as e:
    print(f"❌ Exception occurred: {e}")
