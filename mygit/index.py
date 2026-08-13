"""Handles the staging area (index) - tracks which files are staged
for the next commit, and their blob hashes."""

import os

from . import objects

INDEX_FILE = "index"


def read_index(repo: str) -> dict:
    """Return the current staged entries as {path: blob_sha}."""
    index_path = os.path.join(repo, INDEX_FILE)
    entries = {}

    if not os.path.isfile(index_path):
        return entries

    with open(index_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sha, path = line.split(" ", 1)
            entries[path] = sha

    return entries


def write_index(repo: str, entries: dict):
    """Persist the given {path: blob_sha} entries as the new index."""
    index_path = os.path.join(repo, INDEX_FILE)
    lines = [f"{sha} {path}" for path, sha in sorted(entries.items())]

    with open(index_path, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def add(repo: str, paths):
    """Stage the given files: hash each as a blob and record it in
    the index, keyed by its path relative to the project root (the
    folder containing .mygit) so it works no matter which subfolder
    you run the command from.
    """
    root = os.path.dirname(repo)
    entries = read_index(repo)

    for path in paths:
        abs_path = os.path.abspath(path)
        rel_path = os.path.relpath(abs_path, root).replace(os.sep, "/")

        with open(abs_path, "rb") as f:
            data = f.read()

        sha = objects.hash_object(data, "blob", repo=repo, write=True)
        entries[rel_path] = sha

    write_index(repo, entries)
    return entries


def build_tree_from_index(repo: str, entries: dict) -> str:
    """Convert a flat {path: blob_sha} index into a nested tree
    object - the same way real Git turns the index into a tree at
    commit time. This mirrors tree.write_tree's recursive structure,
    but builds from staged paths instead of walking the filesystem.
    """
    top_files = {}
    top_dirs = {}

    for path, sha in entries.items():
        if "/" in path:
            dirname, rest = path.split("/", 1)
            top_dirs.setdefault(dirname, {})[rest] = sha
        else:
            top_files[path] = sha

    lines = []
    for name in sorted(top_files):
        lines.append(f"100644 blob {top_files[name]}\t{name}")
    for dirname in sorted(top_dirs):
        sub_sha = build_tree_from_index(repo, top_dirs[dirname])
        lines.append(f"40000 tree {sub_sha}\t{dirname}")

    content = ("\n".join(lines) + "\n").encode() if lines else b""
    return objects.hash_object(content, "tree", repo=repo, write=True)
