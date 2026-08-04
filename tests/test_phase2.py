"""Basic correctness tests for Phase 1: init, hash-object, cat-file."""

import os

import pytest

from mygit import objects, repository, tree

# Phase 2 test cases
def test_write_tree_empty_directory(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "empty").mkdir()

    tree_sha = tree.write_tree(repo, str(tmp_path))
    _, content = objects.read_object(repo, tree_sha)
    entries = tree.parse_tree(content)

    assert entries[0]["name"] == "empty"
    assert entries[0]["type"] == "tree"

    _, empty_content = objects.read_object(repo, entries[0]["sha"])
    assert tree.parse_tree(empty_content) == []

def test_write_tree_detects_content_change(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"version one\n")
    sha1 = tree.write_tree(repo, str(tmp_path))

    (tmp_path / "a.txt").write_bytes(b"version two\n")
    sha2 = tree.write_tree(repo, str(tmp_path))

    assert sha1 != sha2

def test_write_tree_structure_affects_hash(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"same content\n")
    flat_sha = tree.write_tree(repo, str(tmp_path))

    (tmp_path / "a.txt").unlink()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_bytes(b"same content\n")
    nested_sha = tree.write_tree(repo, str(tmp_path))

    assert flat_sha != nested_sha

def test_write_tree_handles_multiple_nesting_levels(tmp_path):
    repo = repository.init(str(tmp_path))
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "deep.txt").write_bytes(b"buried\n")

    tree_sha = tree.write_tree(repo, str(tmp_path))

    # Walk down the chain of trees by hand, one level at a time.
    _, content = objects.read_object(repo, tree_sha)
    a_sha = tree.parse_tree(content)[0]["sha"]
    _, content = objects.read_object(repo, a_sha)
    b_sha = tree.parse_tree(content)[0]["sha"]
    _, content = objects.read_object(repo, b_sha)
    c_sha = tree.parse_tree(content)[0]["sha"]
    _, content = objects.read_object(repo, c_sha)
    entries = tree.parse_tree(content)

    assert entries[0]["name"] == "deep.txt"

def test_write_tree_entries_always_sorted(tmp_path):
    repo = repository.init(str(tmp_path))
    # Create in reverse alphabetical order on purpose.
    (tmp_path / "zebra.txt").write_bytes(b"z\n")
    (tmp_path / "apple.txt").write_bytes(b"a\n")
    (tmp_path / "mango.txt").write_bytes(b"m\n")

    tree_sha = tree.write_tree(repo, str(tmp_path))
    _, content = objects.read_object(repo, tree_sha)
    names = [e["name"] for e in tree.parse_tree(content)]

    assert names == ["apple.txt", "mango.txt", "zebra.txt"]