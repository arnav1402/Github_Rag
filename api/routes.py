from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from clone_rag.clone import clone_and_get_files, cleanup
from clone_rag.chunking import chunk_files
from vector_db.pinecone_embedds import ask, embed_and_store, get_namespace, clear_by_namespace

app = FastAPI()

class EmbeddRequest(BaseModel):
    github_url : str

class AskRequest(BaseModel):
    github_url : str
    question : str

class ClearRequest(BaseModel):
    github_url : str

@app.get("/")
def root():
    return {"status": "working"}

@app.post("/rag/embedd")
def embedd_repo(body : EmbeddRequest):
    try:
        print(f"Cloning the {body.github_url}")
        files, repo_path = clone_and_get_files(body.github_url)
        print(f"Getting Files with {len(files)}")

        chunks = chunk_files(files)
        embed_and_store(chunks, body.github_url)

        cleanup(repo_path)

        return {
            "success": True,
            "github_url": body.github_url,
            "files_found": len(files),
            "chunks_stored": len(chunks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/chat")
def ask_rag(body : AskRequest):
    try:
        answer = ask(body.question, body.github_url)
        return {
            "question": body.question,
            "answer": answer,
            "github_url": body.github_url,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/clear_namespace")
def clear_namespace(body : ClearRequest):
    try:
        clear_by_namespace(body.github_url)
        return {
            "success": True,
            "deleted_namespace": get_namespace(body.github_url),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
