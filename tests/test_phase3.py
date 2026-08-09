"""Correctness tests for Phase 3: commit objects and the HEAD chain."""

import os

import pytest

from mygit import commit, objects, repository, tree


def test_write_commit_no_parent(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"a\n")
    tree_sha = tree.write_tree(repo, str(tmp_path))

    commit_sha = commit.write_commit(repo, tree_sha, "first commit")

    obj_type, content = objects.read_object(repo, commit_sha)
    assert obj_type == "commit"

    parsed = commit.parse_commit(content)
    assert parsed["tree"] == tree_sha
    assert parsed["parent"] is None
    assert parsed["message"] == "first commit"


def test_write_commit_with_parent(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"a\n")
    tree_sha1 = tree.write_tree(repo, str(tmp_path))
    commit1 = commit.write_commit(repo, tree_sha1, "first commit")

    (tmp_path / "b.txt").write_bytes(b"b\n")
    tree_sha2 = tree.write_tree(repo, str(tmp_path))
    commit2 = commit.write_commit(repo, tree_sha2, "second commit", parent_sha=commit1)

    _, content = objects.read_object(repo, commit2)
    parsed = commit.parse_commit(content)

    assert parsed["parent"] == commit1
    assert parsed["tree"] == tree_sha2
    assert parsed["message"] == "second commit"


def test_head_starts_empty(tmp_path):
    repo = repository.init(str(tmp_path))
    assert repository.read_head(repo) is None


def test_update_head_and_read_it_back(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"a\n")
    tree_sha = tree.write_tree(repo, str(tmp_path))
    commit_sha = commit.write_commit(repo, tree_sha, "first commit")

    repository.update_head(repo, commit_sha)

    assert repository.read_head(repo) == commit_sha


def test_commit_chain_via_head(tmp_path):
    repo = repository.init(str(tmp_path))

    (tmp_path / "a.txt").write_bytes(b"a\n")
    tree1 = tree.write_tree(repo, str(tmp_path))
    commit1 = commit.write_commit(repo, tree1, "first")
    repository.update_head(repo, commit1)

    (tmp_path / "b.txt").write_bytes(b"b\n")
    tree2 = tree.write_tree(repo, str(tmp_path))
    commit2 = commit.write_commit(repo, tree2, "second", parent_sha=repository.read_head(repo))
    repository.update_head(repo, commit2)

    assert repository.read_head(repo) == commit2

    _, content = objects.read_object(repo, commit2)
    parsed = commit.parse_commit(content)
    assert parsed["parent"] == commit1
