"""Correctness tests for Phase 4: staging area, add, commit, checkout."""

import os

import pytest

from mygit import commit, index, objects, repository, tree


def test_add_stages_a_file(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"hello\n")

    entries = index.add(repo, [str(tmp_path / "a.txt")])

    assert entries == {"a.txt": objects.hash_object(b"hello\n", "blob")}


def test_index_persists_across_read_write(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"hello\n")
    index.add(repo, [str(tmp_path / "a.txt")])

    reloaded = index.read_index(repo)
    assert reloaded == {"a.txt": objects.hash_object(b"hello\n", "blob")}


def test_add_nested_path_uses_forward_slashes(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_bytes(b"nested\n")

    entries = index.add(repo, [str(tmp_path / "sub" / "b.txt")])

    assert "sub/b.txt" in entries


def test_build_tree_from_index_flat(tmp_path):
    repo = repository.init(str(tmp_path))
    sha_a = objects.hash_object(b"a\n", "blob", repo=repo, write=True)
    sha_b = objects.hash_object(b"b\n", "blob", repo=repo, write=True)

    tree_sha = index.build_tree_from_index(repo, {"a.txt": sha_a, "b.txt": sha_b})
    _, content = objects.read_object(repo, tree_sha)
    entries = {e["name"]: e for e in tree.parse_tree(content)}

    assert entries["a.txt"]["sha"] == sha_a
    assert entries["b.txt"]["sha"] == sha_b


def test_build_tree_from_index_nested(tmp_path):
    repo = repository.init(str(tmp_path))
    sha = objects.hash_object(b"nested\n", "blob", repo=repo, write=True)

    tree_sha = index.build_tree_from_index(repo, {"sub/b.txt": sha})
    _, content = objects.read_object(repo, tree_sha)
    top_entries = tree.parse_tree(content)

    assert len(top_entries) == 1
    assert top_entries[0]["name"] == "sub"
    assert top_entries[0]["type"] == "tree"

    _, sub_content = objects.read_object(repo, top_entries[0]["sha"])
    sub_entries = tree.parse_tree(sub_content)
    assert sub_entries[0]["name"] == "b.txt"
    assert sub_entries[0]["sha"] == sha


def test_build_tree_from_index_matches_write_tree(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"a\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_bytes(b"b\n")

    disk_tree_sha = tree.write_tree(repo, str(tmp_path))

    staged = index.add(repo, [str(tmp_path / "a.txt"), str(tmp_path / "sub" / "b.txt")])
    index_tree_sha = index.build_tree_from_index(repo, staged)

    assert disk_tree_sha == index_tree_sha


def test_checkout_tree_restores_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hello\n")
    (src / "sub").mkdir()
    (src / "sub" / "b.txt").write_bytes(b"nested\n")

    repo = repository.init(str(src))
    tree_sha = tree.write_tree(repo, str(src))

    dest = tmp_path / "dest"
    dest.mkdir()
    tree.checkout_tree(repo, tree_sha, str(dest))

    assert (dest / "a.txt").read_bytes() == b"hello\n"
    assert (dest / "sub" / "b.txt").read_bytes() == b"nested\n"


def test_full_add_commit_checkout_roundtrip(tmp_path):
    repo = repository.init(str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"version one\n")

    staged = index.add(repo, [str(tmp_path / "a.txt")])
    tree_sha = index.build_tree_from_index(repo, staged)
    commit_sha = commit.write_commit(repo, tree_sha, "first commit")
    repository.update_head(repo, commit_sha)

    os.remove(tmp_path / "a.txt")
    assert not (tmp_path / "a.txt").exists()

    _, content = objects.read_object(repo, repository.read_head(repo))
    restored_tree_sha = commit.parse_commit(content)["tree"]
    tree.checkout_tree(repo, restored_tree_sha, str(tmp_path))

    assert (tmp_path / "a.txt").read_bytes() == b"version one\n"
