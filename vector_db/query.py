# RAG query with LLM
import logging
import os, sys
from dotenv import load_dotenv
from groq import Groq
from pinecone import Pinecone
from .embeddings import embed_texts, get_namespace, PINECONE_INDEX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    logger.info("Pinecone client initialized for queries")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {str(e)}")
    raise

groq_client = Groq(api_key=GROQ_API_KEY)

def ask(question: str, github_url: str) -> str:
    # Query RAG system and get LLM answer
    try:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
            
        logger.info(f"Processing query: {question[:50]}...")
        index = pc.Index(PINECONE_INDEX)

        # Embed query
        q_vector = embed_texts([question])[0]
        logger.debug("Query embedded")

        # Search Pinecone
        results = index.query(
            vector=q_vector,
            top_k=7,
            namespace=get_namespace(github_url),
            include_metadata=True
        )
        logger.info(f"Retrieved {len(results['matches'])} results")

        # Build context
        if not results["matches"]:
            logger.warning("No matching documents found")
            context = "No relevant code context found."
        else:
            context = "\n\n".join([
                f"File: {m['metadata']['source']}\n{m['metadata']['text']}"
                for m in results["matches"]
            ])

        # Call Groq LLM
        logger.info("Calling Groq LLM")
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a code assistant. Answer questions using only the provided code context. Always mention which file the answer comes from. Explain how each file connects."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}"
                }
            ]
        )
        logger.info("Generated response")
        return response.choices[0].message.content
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to process query: {str(e)}")
        raise
