"""Basic correctness tests for Phase 1: init, hash-object, cat-file."""

import os

import pytest

from mygit import objects, repository


def test_init_creates_expected_structure(tmp_path):
    repo = repository.init(str(tmp_path))

    assert os.path.isdir(os.path.join(repo, "objects"))
    assert os.path.isdir(os.path.join(repo, "refs", "heads"))
    assert os.path.isfile(os.path.join(repo, "HEAD"))

    with open(os.path.join(repo, "HEAD")) as f:
        assert f.read() == "ref: refs/heads/main\n"


def test_init_twice_raises(tmp_path):
    repository.init(str(tmp_path))
    with pytest.raises(repository.RepositoryError):
        repository.init(str(tmp_path))


def test_find_repo_from_subdirectory(tmp_path):
    repo = repository.init(str(tmp_path))
    subdir = tmp_path / "a" / "b" / "c"
    subdir.mkdir(parents=True)

    found = repository.find_repo(str(subdir))
    assert found == repo


def test_hash_object_is_deterministic():
    data = b"hello world\n"
    sha1 = objects.hash_object(data, "blob")
    sha2 = objects.hash_object(data, "blob")
    assert sha1 == sha2
    assert len(sha1) == 40  # SHA-1 hex digest length


def test_hash_object_matches_real_git_blob_hash():
    data = b"hello world\n"
    sha = objects.hash_object(data, "blob")
    assert sha == "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"


def test_write_and_read_object_roundtrip(tmp_path):
    repo = repository.init(str(tmp_path))
    data = b"some file content\n"

    sha = objects.hash_object(data, "blob", repo=repo, write=True)
    obj_type, content = objects.read_object(repo, sha)

    assert obj_type == "blob"
    assert content == data


def test_read_missing_object_raises(tmp_path):
    repo = repository.init(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        objects.read_object(repo, "0" * 40)
