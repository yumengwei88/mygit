"""Handles finding and initializing a .mygit repository."""

import os

REPO_DIR = ".mygit"


class RepositoryError(Exception):
    """Raised for any repository-related error (not found, already exists, etc)."""


def find_repo(start_path=None):
    """Walk upward from start_path (or cwd) looking for a .mygit directory."""

    path = os.path.abspath(start_path or os.getcwd())

    while True:
        candidate = os.path.join(path, REPO_DIR)
        if os.path.isdir(candidate):
            return candidate

        parent = os.path.dirname(path)
        if parent == path:
            # Reached the filesystem root without finding a repo.
            raise RepositoryError(
                "not a mygit repository (or any parent directory up to root)"
            )
        path = parent


def init(path=None):
    """Create a new .mygit repository in path (or cwd).

    Sets up:
      .mygit/objects/       - content-addressable object store
      .mygit/refs/heads/    - branch pointers
      .mygit/HEAD           - points at the current branch
    """
    root = os.path.abspath(path or os.getcwd())
    repo = os.path.join(root, REPO_DIR)

    if os.path.isdir(repo):
        raise RepositoryError(f"repository already exists at {repo}")

    os.makedirs(os.path.join(repo, "objects"))
    os.makedirs(os.path.join(repo, "refs", "heads"))

    with open(os.path.join(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/main\n")

    return repo

def get_head_ref(repo: str) -> str:
    """Return the ref path HEAD currently points to, e.g. 'refs/heads/main'."""

    with open(os.path.join(repo, "HEAD")) as f:
        content = f.read().strip()
    _, _, ref = content.partition(" ")
    return ref

def read_head(repo:str):
    """Return the commit SHA the current branch points to, or None if
    there are no commits yet
    """

    ref_path = os.path.join(repo, get_head_ref(repo))
    if not os.path.isfile(ref_path):
        return None
    with open(ref_path) as f:
        return f.read().strip()

def update_head(repo: str, commit_sha: str):
    """Move the current branch to point at a new commit."""

    ref_path = os.path.join(repo, get_head_ref(repo))
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w") as f:
        f.write(commit_sha + "\n")