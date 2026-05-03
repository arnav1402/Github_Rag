# Embedding generation and storage
import logging
import os, sys
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "gitrag")
PINECONE_CLOUD   = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION  = os.getenv("PINECONE_REGION", "us-east-1")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY environment variable not set")

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    logger.info("Pinecone client initialized")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {str(e)}")
    raise

# GPU setup
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

EMBED_MODEL = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
EMBED_MODEL = EMBED_MODEL.to(device)
DIMENSION   = 768
BATCH_SIZE = 128
UPSERT_BATCH_SIZE = 5  # Upsert every 5 batches

def get_namespace(github_url: str) -> str:
    # Convert GitHub URL to namespace (owner/repo)
    return github_url.replace("https://github.com/", "").replace(".git", "")

def get_or_create_index() -> object:
    # Get existing index or create if not exists
    try:
        existing = [i.name for i in pc.list_indexes()]
        if PINECONE_INDEX not in existing:
            logger.info(f"Creating index: {PINECONE_INDEX}")
            pc.create_index(
                name=PINECONE_INDEX,
                dimension=DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
            )
            logger.info(f"Created index: {PINECONE_INDEX}")
        else:
            logger.info(f"Using existing index: {PINECONE_INDEX}")
        return pc.Index(PINECONE_INDEX)
    except Exception as e:
        logger.error(f"Failed to get/create index: {str(e)}")
        raise

def embed_texts(texts: list[str]) -> list[list[float]]:
    # Generate embeddings on GPU/CPU
    try:
        if not texts:
            raise ValueError("Cannot embed empty text list")
        embeddings = EMBED_MODEL.encode(texts, convert_to_numpy=True, device=device)
        logger.debug(f"Generated {len(texts)} embeddings on {device}")
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Failed to embed texts: {str(e)}")
        raise

def clear_by_namespace(github_url: str):
    # Delete all vectors in a namespace
    try:
        index = pc.Index(PINECONE_INDEX)
        namespace = get_namespace(github_url)
        index.delete(delete_all=True, namespace=namespace)
        logger.info(f"Cleared namespace: {namespace}")
    except Exception as e:
        logger.error(f"Failed to clear namespace: {str(e)}")
        raise

def embed_and_store(chunks: list[dict], github_url: str):
    # Embed and store with batched upserts
    try:
        if not chunks:
            logger.warning("No chunks provided for embedding")
            return
            
        index = get_or_create_index()
        total = len(chunks)
        logger.info(f"Embedding {total} chunks (batch size: {BATCH_SIZE})")

        all_upsert_data = []
        embed_batch_count = 0
        
        for i in range(0, total, BATCH_SIZE):
            try:
                batch = chunks[i : i + BATCH_SIZE]
                texts = [c["text"] for c in batch]
                vectors = embed_texts(texts)
                
                # Accumulate upsert data
                for c, vec in zip(batch, vectors):
                    all_upsert_data.append((c["id"], vec, {"text": c["text"], "source": c["source"]}))
                
                embed_batch_count += 1
                
                # Upsert every 5 embedding batches or at end
                should_upsert = (embed_batch_count % UPSERT_BATCH_SIZE == 0) or (i + BATCH_SIZE >= total)
                if should_upsert:
                    index.upsert(vectors=all_upsert_data, namespace=get_namespace(github_url))
                    upserts_done = (i // BATCH_SIZE) + 1
                    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
                    logger.info(f"Upserted up to batch {upserts_done}/{total_batches} ({len(all_upsert_data)} chunks)")
                    all_upsert_data = []
                    
            except Exception as e:
                logger.error(f"Failed at batch {i}: {str(e)}")
                raise

        logger.info(f"Successfully stored {total} chunks")
    except Exception as e:
        logger.error(f"Failed to embed and store: {str(e)}")
        raise

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from clone_rag.clone import clone_and_get_files, cleanup
    from clone_rag.chunking import chunk_files

    try:
        url = "https://github.com/arnav1402/Django-React-Auth-Boilerplate.git"
        logger.info(f"Cloning {url}")
        files, repo_path = clone_and_get_files(url)
        logger.info(f"Found {len(files)} files")
        chunks = chunk_files(files)
        embed_and_store(chunks, url)
        cleanup(repo_path)
        logger.info("Embedding complete")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}", exc_info=True)
