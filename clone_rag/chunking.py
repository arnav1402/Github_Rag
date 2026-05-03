# Text chunking utilities for code files
import logging
import os, sys
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

logger = logging.getLogger(__name__)
sys.path.append(os.path.dirname(__file__))

ext_to_lang = {
    ".py":   Language.PYTHON,
    ".js":   Language.JS,
    ".jsx":  Language.JS,
    ".ts":   Language.JS,
    ".tsx":  Language.JS,
    ".cpp":  Language.CPP,
    ".c":    Language.C,
    ".java": Language.JAVA,
    ".rs":   Language.RUST,
    ".go":   Language.GO,
    ".html": Language.HTML,
}

def chunk_files(files : list[dict], chunk_size: int=600, chunk_overlap : int=60)->list[dict]:
    # Split code files into semantic chunks
    chunks = []
    skipped = 0
    
    try:
        for f in files:
            ext = "."+f["path"].split(".")[-1] if "." in f["path"] else ""
            lang = ext_to_lang.get(ext)

            if not f["content"].strip():
                skipped += 1
                continue

            try:
                if lang:
                    splitter = RecursiveCharacterTextSplitter.from_language(
                        language=lang,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                else:
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )

                parts = splitter.split_text(f["content"])
                for i, part in enumerate(parts):
                    chunks.append({
                        "id": f"{f['path']}::chunk{i}",
                        "text": part,
                        "source": f["path"]
                    })
                logger.debug(f"Chunked {f['path']} into {len(parts)} chunks")
            except Exception as e:
                logger.warning(f"Failed to chunk {f['path']}: {str(e)}")
                continue

        logger.info(f"Created {len(chunks)} chunks from {len(files)} files (skipped {skipped} empty files)")
        return chunks
    except Exception as e:
        logger.error(f"Failed to chunk files: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from clone import clone_and_get_files, cleanup

    try:
        files, repo_path = clone_and_get_files("https://github.com/arnav1402/uber_dav.git")
        logger.info(f"Files found: {len(files)}")

        chunks = chunk_files(files)
        for c in chunks[:5]:
            logger.info(f"{c['id']}: {c['text'][:100]}...")

        cleanup(repo_path)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}", exc_info=True)