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
