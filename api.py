# FastAPI backend for GitRAG system
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import os, sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from models import EmbeddingRequest, AskRequest, ClearRequest
from clone_rag.clone import clone_and_get_files, cleanup
from clone_rag.chunking import chunk_files
from vector_db.embeddings import embed_and_store, get_namespace, clear_by_namespace
from vector_db.query import ask

app = FastAPI(title="GitRAG API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def validate_github_url(url: str) -> None:
    if not url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL: must start with https://github.com/")
    if not url.endswith(".git"):
        raise ValueError("Invalid GitHub URL: must end with .git")

def validate_question(question: str) -> None:
    if not question or len(question.strip()) == 0:
        raise ValueError("Question cannot be empty")
    if len(question) > 5000:
        raise ValueError("Question too long (max 5000 chars)")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"status": "working", "service": "GitRAG API"}

@app.post("/rag/embedd")
def embedd_repo(body: EmbeddingRequest):
    try:
        validate_github_url(body.github_url)
        logger.info(f"Starting embedding for {body.github_url}")
        files, repo_path = clone_and_get_files(body.github_url)
        logger.info(f"Cloned. Found {len(files)} files")
        chunks = chunk_files(files)
        logger.info(f"Created {len(chunks)} chunks")
        embed_and_store(chunks, body.github_url)
        cleanup(repo_path)
        logger.info(f"Embedding completed for {body.github_url}")
        return {"success": True, "github_url": body.github_url, "files_found": len(files), "chunks_stored": len(chunks)}
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to embed: {str(e)}")

@app.post("/rag/chat")
def ask_rag(body: AskRequest):
    try:
        validate_github_url(body.github_url)
        validate_question(body.question)
        logger.info(f"Query: {body.question[:50]}...")
        answer = ask(body.question, body.github_url)
        logger.info("Answer generated")
        return {"question": body.question, "answer": answer, "github_url": body.github_url}
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process query: {str(e)}")

@app.post("/rag/clear_namespace")
def clear_namespace(body: ClearRequest):
    try:
        validate_github_url(body.github_url)
        logger.info(f"Clearing namespace for {body.github_url}")
        clear_by_namespace(body.github_url)
        namespace = get_namespace(body.github_url)
        logger.info(f"Cleared namespace: {namespace}")
        return {"success": True, "deleted_namespace": namespace}
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Clear error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to clear: {str(e)}")

if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app, host="127.0.0.1", port=8000)