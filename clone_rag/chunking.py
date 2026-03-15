from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import os, sys
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
    chunks = []
    for f in files:
        ext = "."+f["path"].split(".")[-1] if "." in f["path"] else ""
        lang = ext_to_lang.get(ext)

        if not f["content"].strip():
            continue

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

    print(f"Total chunks created {len(chunks)}")
    return chunks

if __name__ == "__main__":
    from clone import clone_and_get_files, cleanup

    files, repo_path = clone_and_get_files("https://github.com/arnav1402/uber_dav.git")
    print(f"Files found {len(files)}")
    print(repo_path)

    chunks = chunk_files(files)
    for c in chunks[:5]:
        print(f"\n--- {c['id']} ---\n{c['text'][:200]}")

    cleanup(repo_path)