"""Handles Git's content-addressable object storage.

Every object (blob, tree, commit) is stored the same way:
  1. Prefix the raw content with a header: "<type> <size>\\0"
  2. Hash the whole thing (header + content) with SHA-1 -> that's the object's ID
  3. Compress it with zlib and write it to objects/<sha[:2]>/<sha[2:]>

This is what makes Git "content-addressable": two files with identical
content always produce the identical hash and are stored only once.
"""

import hashlib
import os
import zlib


def hash_object(data: bytes, obj_type: str, repo: str = None, write: bool = False) -> str:
    """Compute the SHA-1 hash for data, optionally writing it to the object store."""
    
    header = f"{obj_type} {len(data)}\0".encode()
    full_data = header + data
    sha = hashlib.sha1(full_data).hexdigest()

    if write:
        if repo is None:
            raise ValueError("repo path is required when write=True")

        obj_dir = os.path.join(repo, "objects", sha[:2])
        obj_path = os.path.join(obj_dir, sha[2:])

        if not os.path.exists(obj_path):
            os.makedirs(obj_dir, exist_ok=True)
            compressed = zlib.compress(full_data)
            with open(obj_path, "wb") as f:
                f.write(compressed)

    return sha


def read_object(repo: str, sha: str):
    """Read an object back out of the store given its hash.

    Returns:
        (obj_type, content) tuple, where content is raw bytes.
    """
    obj_path = os.path.join(repo, "objects", sha[:2], sha[2:])

    if not os.path.isfile(obj_path):
        raise FileNotFoundError(f"object {sha} not found")

    with open(obj_path, "rb") as f:
        full_data = zlib.decompress(f.read())

    header, _, content = full_data.partition(b"\0")
    obj_type, size_str = header.decode().split(" ")
    size = int(size_str)

    if len(content) != size:
        raise ValueError(f"object {sha} is corrupted: size mismatch")

    return obj_type, content
