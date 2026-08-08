"""Handles building and reading commit objects.

A commit object ties a tree snapshot to a point in project history: it
records which tree it snapshots, which commit (if any) came directly
before it, who made it and when, and a message describing the change.
"""

import time

from . import objects

def write_commit(repo: str, tree_sha: str, message: str, parent_sha: str = None, author: str = "mygit user") -> str:
    """Create and store a commit object. Returns its SHA"""
    lines = [f"tree {tree_sha}"]

    if parent_sha:
        lines.append(f"parent {parent_sha}")

    timestamp = int(time.time())
    lines.append(f"author {author} {timestamp}")
    lines.append("")
    lines.append(message)

    content = ("\n".join(lines) + "\n").encode()
    return objects.hash_object(content, "commit", repo=repo, write=True)

def parse_commit(content: bytes) -> dict:
    """Parse a commit object's raw content into a dict.
    
    Returns a dict with keys: tree, parent (None if there isn't one),
    author, timestamp, message.
    """
    text = content.decode()
    header_text, _, message = text.partition("\n\n")

    result = {"parent": None}

    for line in header_text.splitlines():
        key, _, value = line.partition(" ")
        if key == "tree":
            result["tree"] = value
        elif key == "parent":
            result["parent"] = value
        elif key == "author":
            name, _, timestamp_str = value.rpartition(" ")
            result["author"] = name
            result["timestamp"] = int(timestamp_str)

    result["message"] = message.rstrip("\n")
    return result
            
