"""Handles building and reading tree objects."""
import os

from . import objects

IGNORED_DIRS = {".mygit", ".git", "__pycache__", ".venv", "venv"}


def write_tree(repo: str, path: str = ".") -> str:
    """Recursively snapshot a directory into blob/tree objects"""

    entries = []

    for name in sorted(os.listdir(path)):
        if name in IGNORED_DIRS:
            continue

        full_path = os.path.join(path, name)

        if os.path.isdir(full_path):
            sha = write_tree(repo, full_path)
            mode = "40000"
            obj_type = "tree"
        else:
            with open(full_path, "rb") as f:
                data = f.read()
            sha = objects.hash_object(data, "blob", repo=repo, write=True)
            mode = "100644"
            obj_type = "blob"

        entries.append(f"{mode} {obj_type} {sha}\t{name}")

    tree_content = ("\n".join(entries) + "\n").encode() if entries else b""
    return objects.hash_object(tree_content, "tree", repo=repo, write=True)
