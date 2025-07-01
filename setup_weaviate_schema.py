import weaviate

client = weaviate.Client(
    url="https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud",
    auth_client_secret=weaviate.AuthApiKey("dFovQ01lNVRoUjdEOCtrRV9EQVlKd29GK1ZnWmNiclpFbmxSK2gxTjBrODBSMEZWVVQwMFBtSFhNYUVBPV92MjAw"),  
)

class_obj = {
    "class": "SpeechChunk",
    "vectorizer": "none",
    "vectorIndexConfig": {
        "distance": "cosine"
    },
    "properties": [
        {"name": "chunk_id", "dataType": ["text"]},
        {"name": "source_type", "dataType": ["text"]},
        {"name": "chunk_index", "dataType": ["int"]},
        {"name": "text", "dataType": ["text"]},
        {"name": "laureate", "dataType": ["text"]},
        {"name": "year_awarded", "dataType": ["int"]},
        {"name": "category", "dataType": ["text"]},
        {"name": "gender", "dataType": ["text"]},
        {"name": "country", "dataType": ["text"]},
        {"name": "specific_work_cited", "dataType": ["boolean"]},
        {"name": "prize_motivation", "dataType": ["text"]},
        {"name": "lastname", "dataType": ["text"]}
    ]
}

# Create the schema
client.schema.create_class(class_obj)
