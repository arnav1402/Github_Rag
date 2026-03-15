import subprocess, os, tempfile, shutil, stat

def clone(github_url :str) -> str:
    temp = tempfile.mkdtemp()
    subprocess.run(["git", "clone", "--depth=1", github_url, temp], check=True)
    return temp

def get_files(repo_path: str)->list[dict]:
    extensions = {".py", ".js", ".ts", ".go", ".java", ".rs", ".cpp", ".md", ".jsx", ".tsx", ".c", ".html", ".css"}
    files = []
    for root, _, filenames in os.walk(repo_path):
        if ".git" in root:
            continue
        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                full_path = os.path.join(root, fname)
                with open(full_path, "r", errors="ignore") as f:
                    files.append({
                        "path": os.path.relpath(full_path, repo_path),
                        "content": f.read()
                    })
    return files

def force_remove_repo(func, path, exec):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_and_get_files(github_url: str) -> tuple[list[dict], str]:
    repo_path = clone(github_url)
    files = get_files(repo_path)
    return files, repo_path

def get_namespace(github_url: str) -> str:
    return github_url.replace("https://github.com/", "").replace(".git", "")

def cleanup(repo_path: str):
    shutil.rmtree(repo_path, onexc=force_remove_repo)
    print(f"Cleaned up {repo_path}")

if __name__ == "__main__":
    repo_path = clone("https://github.com/arnav1402/uber_dav.git")
    files = get_files(repo_path)
    print(f"Cloned {len(files)} files")
    print(repo_path)
    for f in files:
        print(f["path"])
    cleanup(repo_path)
    print("Cleaned the cache")