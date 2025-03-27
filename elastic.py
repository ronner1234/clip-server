
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, bulk
import re

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")  # Modify the host if needed
INDEX_NAME = "image_embeddings_clip"

def extract_page_number(uri: str) -> int:
    """Extracts the page number from the image URI."""
    match = re.search(r'image_(\d+)_\d+', uri)
    return int(match.group(1)) if match else None

def update_documents():
    """Fetches documents, extracts page number, and updates Elasticsearch."""
    query = {"query": {"exists": {"field": "uri"}}}  # Ensure `uri` exists in the document
    docs_to_update = []

    for doc in scan(es, index=INDEX_NAME, query=query):
        doc_id = doc["_id"]
        uri = doc["_source"].get("uri", "")

        if uri:
            page_number = extract_page_number(uri)
            if page_number is not None:
                docs_to_update.append({
                    "_op_type": "update",
                    "_index": INDEX_NAME,
                    "_id": doc_id,
                    "doc": {"page_number": page_number},
                })

    if docs_to_update:
        bulk(es, docs_to_update)
        print(f"Updated {len(docs_to_update)} documents with page_number.")

if __name__ == "__main__":
    update_documents()
