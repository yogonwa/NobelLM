import weaviate
from weaviate.auth import AuthApiKey

client = weaviate.Client(
    url="https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud",
    auth_client_secret=AuthApiKey("WHFkaTc4b1hWZ2EzdVJ6MF9uV3V4dTM2U0g5QVlxak83WnBVd1hFZnl3VFRwS3Y2SDB4LzBDSXdhaHBZPV92MjAw")
)

schema = client.schema.get()

speech_chunk_config = next(
    (cls for cls in schema['classes'] if cls['class'] == 'SpeechChunk'),
    None
)

if speech_chunk_config:
    print("✅ SpeechChunk vectorizer config:")
    print(f"Vectorizer: {speech_chunk_config.get('vectorizer')}")
    print("Module config:", speech_chunk_config.get('moduleConfig'))
else:
    print("❌ SpeechChunk class not found")
