# Git repository cloning and file extraction utilities
import logging
import subprocess, os, tempfile, shutil, stat

logger = logging.getLogger(__name__)

def clone(github_url :str) -> str:
    # Clone GitHub repo to temp directory
    try:
        temp = tempfile.mkdtemp()
        logger.info(f"Cloning {github_url} to {temp}")
        subprocess.run(
            ["git", "clone", "--depth=1", github_url, temp],
            check=True,
            capture_output=True,
            timeout=300
        )
        logger.info(f"Successfully cloned")
        return temp
    except subprocess.TimeoutExpired:
        logger.error(f"Clone timeout for {github_url}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Clone failed: {e.stderr.decode()}")
        raise

def get_files(repo_path: str)->list[dict]:
    # Extract code files from repository
    extensions = {".py", ".js", ".ts", ".go", ".java", ".rs", ".cpp", ".md", ".jsx", ".tsx", ".c", ".html", ".css"}
    files = []
    try:
        for root, _, filenames in os.walk(repo_path):
            if ".git" in root:
                continue
            for fname in filenames:
                if any(fname.endswith(ext) for ext in extensions):
                    full_path = os.path.join(root, fname)
                    try:
                        with open(full_path, "r", errors="ignore") as f:
                            content = f.read()
                            if content.strip():
                                files.append({"path": os.path.relpath(full_path, repo_path), "content": content})
                    except Exception as e:
                        logger.warning(f"Failed to read {full_path}: {str(e)}")
                        continue
        logger.info(f"Extracted {len(files)} files")
        return files
    except Exception as e:
        logger.error(f"Failed to extract files: {str(e)}")
        raise

def force_remove_repo(func, path, exc):
    # Helper for forceful directory removal
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        logger.warning(f"Failed to remove {path}: {str(e)}")

def clone_and_get_files(github_url: str) -> tuple[list[dict], str]:
    # Clone repo and extract files
    try:
        repo_path = clone(github_url)
        files = get_files(repo_path)
        return files, repo_path
    except Exception as e:
        logger.error(f"Failed to clone and get files: {str(e)}")
        raise

def cleanup(repo_path: str):
    # Clean up temp directory
    try:
        shutil.rmtree(repo_path, onexc=force_remove_repo)
        logger.info(f"Cleaned up {repo_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        repo_path = clone("https://github.com/arnav1402/uber_dav.git")
        files = get_files(repo_path)
        logger.info(f"Cloned {len(files)} files")
        for f in files[:5]:
            logger.info(f["path"])
        cleanup(repo_path)
        logger.info("Cleanup complete")
    except Exception as e:
        logger.error(f"Script failed: {str(e)}", exc_info=True)