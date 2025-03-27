from fastapi import FastAPI, HTTPException, Query, UploadFile, File, APIRouter
from clip_client import Client
from docarray import Document
import os
from elasticsearch import Elasticsearch
from typing import Annotated, List, Union

router = APIRouter(tags=["Search"])

os.environ["GRPC_ARG_KEEPALIVE_TIME_MS"] = "60000"  # Ping every 60 seconds
os.environ["GRPC_ARG_KEEPALIVE_TIMEOUT_MS"] = "20000"  # Wait 20 seconds for response

c = Client('grpc://6.tcp.ngrok.io:16605')
c.profile()

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://localhost:9200"])

# Define the index name
index_name = 'image_embeddings_clip'

def search_elasticsearch(query_vector: List[float], limit: int, offset: int, file_names: List[str] = None):
    search_body = {
        "size": limit,
        "from": offset,
        "query": {
            "script_score": {
                "query": {
                    "bool": {
                        "must": [{"match_all": {}}],
                        "filter": [{"terms": {"file_name": file_names}}] if file_names else []
                    }
                },
                "script": {
                    "source": "return cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_vector}
                }
            }
        }
    }
    response = es.search(index=index_name, body=search_body)
    return [Document(uri=hit['_source']['uri'], tags={"file_name": hit['_source']['file_name'], "page_number": hit['_source']['page_number']}) for hit in response['hits']['hits'] if hit['_source']['uri'].endswith(('png', 'jpg', 'jpeg'))]

@router.get("/search/text")
async def search_text(query: str, limit: int = Query(30, gt=0), offset: int = Query(0, ge=0), file_names: Annotated[Union[list[str], None], Query()] = None):
    print(file_names)
    if file_names:
        file_names = [f if f.endswith('.pdf') else f"{f}.pdf" for f in file_names]
    vec = c.encode([query])
    query_vector = vec[0].tolist()  # Convert numpy array to list
    results = search_elasticsearch(query_vector, limit, offset, file_names)
    print(results)
    result_rerank = c.rank([Document(text=query, matches=results)])
    reranked_results = [
        {"uri": match.uri.lstrip('.'), "score": match.scores['clip_score'].value, "file_name": match.tags['file_name'], "page_number": match.tags['page_number']} 
        for match in result_rerank[0].matches
        ]
    return reranked_results

@router.post("/search/image")
async def search_image(file: UploadFile = File(...), limit: int = Query(30, gt=0), offset: int = Query(0, ge=0), file_names: Annotated[Union[list[str], None], Query()] = None):
    if file_names:
        file_names = [f if f.endswith('.pdf') else f"{f}.pdf" for f in file_names]
    if not file.filename.endswith(('png', 'jpg', 'jpeg')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    image_bytes = await file.read()
    vec = c.encode([Document(blob=image_bytes)])
    query_vector = vec[0].embedding
    results = search_elasticsearch(query_vector, limit, offset, file_names)
    result_rerank = c.rank([Document(blob=image_bytes, matches=results)])
    reranked_results = [
        {"uri": match.uri.lstrip('.'), "score": match.scores['clip_score'].value, "file_name": match.tags['file_name'], "page_number": match.tags['page_number']} 
        for match in result_rerank[0].matches
        ]
    return reranked_results


# @router.post("/search/image")
# async def mock_image(file: UploadFile = File(...), limit: int = Query(30, gt=0), offset: int = Query(0, ge=0)):
#     return [
#         {"uri": "/images/image_90_1.png", "score": 0.16, "file_name": "Serax.pdf", "page_number": 90}, 
#         {"uri": "/images/image_91_1.png", "score": 0.15, "file_name": "Serax.pdf", "page_number": 91},
#         {"uri": "/images/image_93_3.png", "score": 0.14, "file_name": "Serax.pdf", "page_number": 93},
#         {"uri": "/images/image_103_4.png", "score": 0.12, "file_name": "Serax.pdf", "page_number": 103},
#         {"uri": "/images/image_104_2.png", "score": 0.11, "file_name": "Serax.pdf", "page_number": 104},
#         {"uri": "/images/image_105_2.png", "score": 0.10, "file_name": "Serax.pdf", "page_number": 105},
#         {"uri": "/images/image_106_4.png", "score": 0.09, "file_name": "Serax.pdf", "page_number": 106},
#         {"uri": "/images/image_98_8.png", "score": 0.07, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_150_1.png", "score": 0.04, "file_name": "Serax.pdf", "page_number": 150},
#         {"uri": "/images/image_99_1.png", "score": 0.02, "file_name": "Serax.pdf", "page_number": 99},
#         {"uri": "/images/image_98_1.png", "score": 0.16, "file_name": "Serax.pdf", "page_number": 98}, 
#         {"uri": "/images/image_98_2.png", "score": 0.15, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_3.png", "score": 0.14, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_4.png", "score": 0.12, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_5.png", "score": 0.11, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_6.png", "score": 0.10, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_7.png", "score": 0.09, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_8.png", "score": 0.07, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_9.png", "score": 0.04, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_99_1.png", "score": 0.02, "file_name": "Serax.pdf", "page_number": 99},
#         {"uri": "/images/image_98_1.png", "score": 0.16, "file_name": "Serax.pdf", "page_number": 98}, 
#         {"uri": "/images/image_98_2.png", "score": 0.15, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_3.png", "score": 0.14, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_4.png", "score": 0.12, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_5.png", "score": 0.11, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_6.png", "score": 0.10, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_7.png", "score": 0.09, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_8.png", "score": 0.07, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_9.png", "score": 0.04, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_99_1.png", "score": 0.02, "file_name": "Serax.pdf", "page_number": 99},
#         {"uri": "/images/image_98_1.png", "score": 0.16, "file_name": "Serax.pdf", "page_number": 98}, 
#         {"uri": "/images/image_98_2.png", "score": 0.15, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_3.png", "score": 0.14, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_4.png", "score": 0.12, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_5.png", "score": 0.11, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_6.png", "score": 0.10, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_7.png", "score": 0.09, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_8.png", "score": 0.07, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_9.png", "score": 0.04, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_99_1.png", "score": 0.02, "file_name": "Serax.pdf", "page_number": 99}
#     ]


# @router.get("/search/text")
# async def mock_text(query: str, limit: int = Query(30, gt=0), offset: int = Query(0, ge=0)):
#     return [
#         {"uri": "/images/image_90_1.png", "score": 0.16, "file_name": "Serax.pdf", "page_number": 90}, 
#         {"uri": "/images/image_91_1.png", "score": 0.15, "file_name": "Serax.pdf", "page_number": 91},
#         {"uri": "/images/image_93_3.png", "score": 0.14, "file_name": "Serax.pdf", "page_number": 93},
#         {"uri": "/images/image_103_4.png", "score": 0.12, "file_name": "Serax.pdf", "page_number": 103},
#         {"uri": "/images/image_104_2.png", "score": 0.11, "file_name": "Serax.pdf", "page_number": 104},
#         {"uri": "/images/image_105_2.png", "score": 0.10, "file_name": "Serax.pdf", "page_number": 105},
#         {"uri": "/images/image_106_4.png", "score": 0.09, "file_name": "Serax.pdf", "page_number": 106},
#         {"uri": "/images/image_98_8.png", "score": 0.07, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_150_1.png", "score": 0.04, "file_name": "Serax.pdf", "page_number": 150},
#         {"uri": "/images/image_99_1.png", "score": 0.02, "file_name": "Serax.pdf", "page_number": 99},
#         {"uri": "/images/image_98_1.png", "score": 0.16, "file_name": "Serax.pdf", "page_number": 98}, 
#         {"uri": "/images/image_98_2.png", "score": 0.15, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_3.png", "score": 0.14, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_4.png", "score": 0.12, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_5.png", "score": 0.11, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_6.png", "score": 0.10, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_7.png", "score": 0.09, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_8.png", "score": 0.07, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_9.png", "score": 0.04, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_99_1.png", "score": 0.02, "file_name": "Serax.pdf", "page_number": 99},
#         {"uri": "/images/image_98_1.png", "score": 0.16, "file_name": "Serax.pdf", "page_number": 98}, 
#         {"uri": "/images/image_98_2.png", "score": 0.15, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_3.png", "score": 0.14, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_4.png", "score": 0.12, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_5.png", "score": 0.11, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_6.png", "score": 0.10, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_7.png", "score": 0.09, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_8.png", "score": 0.07, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_98_9.png", "score": 0.04, "file_name": "Serax.pdf", "page_number": 98},
#         {"uri": "/images/image_99_1.png", "score": 0.02, "file_name": "Serax.pdf", "page_number": 99}
#     ]