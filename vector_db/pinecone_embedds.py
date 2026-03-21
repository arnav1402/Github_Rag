import os, sys
from dotenv import load_dotenv
from bytez import Bytez
from pinecone import Pinecone, ServerlessSpec

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

BYTEZ_API_KEY    = os.getenv("BYTEZ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "gitrag")
PINECONE_CLOUD   = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION  = os.getenv("PINECONE_REGION", "us-east-1")

sdk = Bytez(BYTEZ_API_KEY)
pc  = Pinecone(api_key=PINECONE_API_KEY)

EMBED_MODEL = "sentence-transformers/all-mpnet-base-v2"  # outputs 768
DIMENSION   = 768
BATCH_SIZE    = 32
 
def get_namespace(github_url: str) -> str:
    return github_url.replace("https://github.com/", "").replace(".git", "")

def get_or_create_index() -> object:
    existing = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )
        print(f"Created Pinecone index: {PINECONE_INDEX}")
    else:
        print(f"Using existing index: {PINECONE_INDEX}")
    return pc.Index(PINECONE_INDEX)

def embed_texts(texts: list[str]) -> list[list[float]]:
    embed_model = sdk.model(EMBED_MODEL)
    results = embed_model.run(texts)
    if results.error:
        raise RuntimeError(f"Embedding error: {results.error}")
    return results.output

def clear_by_namespace(github_url : str):
    index = pc.Index(PINECONE_INDEX)
    namespace = get_namespace(github_url)
    index.delete(delete_all=True, namespace=namespace)
    print(f"Deleted all vectors in {namespace}")


def embed_and_store(chunks: list[dict], github_url: str):
    index = get_or_create_index()
    total = len(chunks)

    for i in range(0, total, BATCH_SIZE):
        batch    = chunks[i : i + BATCH_SIZE]
        texts    = [c["text"] for c in batch]
        vectors  = embed_texts(texts)

        upsert_data = [
            (
                c["id"],
                vec,
                {"text": c["text"], "source": c["source"]},
            )
            for c, vec in zip(batch, vectors)
        ]
        index.upsert(vectors=upsert_data, namespace=get_namespace(github_url))
        batch_num     = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Upserted batch {batch_num}/{total_batches}  ({len(batch)} chunks)")
    print(f"\nDone — {total} chunks stored in Pinecone index '{PINECONE_INDEX}'")

def ask(question: str, github_url: str):
    index = pc.Index(PINECONE_INDEX)

    q_vector = embed_texts([question])[0]

    # search pinecone for top 5 most relevant chunks
    results = index.query(vector=q_vector, top_k=7, namespace=get_namespace(github_url=github_url), include_metadata=True)

    context = "\n\n".join([
        f"File: {m['metadata']['source']}\n{m['metadata']['text']}"
        for m in results["matches"]
    ])

    llm = sdk.model("openai/gpt-4o")
    response = llm.run([
        {
            "role": "system",
            "content": "You are a code assistant. Answer questions using only the provided code context. Always mention which file the answer comes from. Explain how each file gets connected to each other"
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}"
        }
    ])

    if response.error:
        raise RuntimeError(f"LLM error: {response.error}")

    output = response.output
    if isinstance(output, dict):
        output = output.get("content") or str(output)
    return output

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from clone_rag.clone import clone_and_get_files, cleanup
    from clone_rag.chunking import chunk_files

    url = "https://github.com/arnav1402/Django-React-Auth-Boilerplate.git"
    print(f"Cloning {url} ...")
    files, repo_path = clone_and_get_files(url)

    print(f"Found {len(files)} files")
    chunks = chunk_files(files)

    embed_and_store(chunks, url)
    cleanup(repo_path)

    print("\n--- Test query ---")
    answer = ask("What APIs does this repo expose?", url)
    print(answer)