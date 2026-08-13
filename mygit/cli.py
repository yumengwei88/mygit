"""Command-line interface for mygit."""

import argparse
import sys
import os
import time

from . import objects
from . import repository
from . import tree
from . import commit
from . import index

def cmd_init(args):
    try:
        repo = repository.init(args.path)
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"initialized empty mygit repository in {repo}")


def cmd_hash_object(args):
    repo = None
    if args.write:
        try:
            repo = repository.find_repo()
        except repository.RepositoryError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

    with open(args.file, "rb") as f:
        data = f.read()

    sha = objects.hash_object(data, "blob", repo=repo, write=args.write)
    print(sha)

def cmd_cat_file(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        obj_type, content = objects.read_object(repo, args.sha)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.type:
        print(obj_type)
    elif args.size:
        print(len(content))
    elif args.pretty:
        sys.stdout.buffer.write(content)
    else:
        print("error: must specify -t, -s, or -p", file=sys.stderr)
        sys.exit(1)

# Phase 2 begins
def cmd_write_tree(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    sha = tree.write_tree(repo, args.path)
    print(sha)

def cmd_ls_tree(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        obj_type, content = objects.read_object(repo, args.sha)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    if obj_type != "tree":
        print(f"error: object {args.sha} is not a tree, it's a {obj_type}", file = sys.stderr)
        sys.exit(1)

    for entry in tree.parse_tree(content):
        print(f"{entry['mode']} {entry['type']} {entry['sha']}\t{entry['name']}")

# Phase 2 ends
# Phase 3 beings
def cmd_commit_tree(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    sha = commit.write_commit(repo, args.tree, args.message, parent_sha=args.parent)
    print(sha)

def cmd_update_ref(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    repository.update_head(repo, args.sha)

def cmd_rev_parse(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.ref != "HEAD":
        print("error: only 'HEAD' is supported right now", file=sys.stderr)
        sys.exit(1)

    sha = repository.read_head(repo)
    if sha is None:
        print("error: HEAD has no commits yet", file=sys.stderr)
        sys.exit(1)

    print(sha)

# Phase 3 end
# Phase 4 begins
def cmd_add(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    for path in args.files:
        if not os.path.isfile(path):
            print(f"error: {path} is not a file (directories aren't supported by add)", file=sys.stderr)
            sys.exit(1)

    index.add(repo, args.files)
    print(f"staged {len(args.files)} file(s)")

def cmd_commit(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    entries = index.read_index(repo)
    if not entries:
        print("error: nothing staged (use 'mygit add <file>' first)", file=sys.stderr)
        sys.exit(1)

    tree_sha = index.build_tree_from_index(repo, entries)
    parent_sha = repository.read_head(repo)

    commit_sha = commit.write_commit(repo, tree_sha, args.message, parent_sha=parent_sha)
    repository.update_head(repo, commit_sha)
    print(commit_sha)
# Phase 4 end

def main():
    parser = argparse.ArgumentParser(prog="mygit", description="A minimal Git implementation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_init = subparsers.add_parser("init", help="create a new repository")
    p_init.add_argument(
        "path", nargs="?", default=None,
        help="directory to initialize (default: current directory)"
    )
    p_init.set_defaults(func=cmd_init)

    p_hash = subparsers.add_parser("hash-object", help="compute object hash for a file")
    p_hash.add_argument("file", help="file to hash")
    p_hash.add_argument(
        "-w", "--write", action="store_true",
        help="write the object to the object store"
    )
    p_hash.set_defaults(func=cmd_hash_object)

    p_cat = subparsers.add_parser("cat-file", help="show contents of a repository object")
    p_cat.add_argument("sha", help="object hash")
    group = p_cat.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", dest="type", action="store_true", help="show object type")
    group.add_argument("-s", dest="size", action="store_true", help="show object size")
    group.add_argument("-p", dest="pretty", action="store_true", help="pretty-print object content")
    p_cat.set_defaults(func=cmd_cat_file)

    # Phase 2 begins
    p_write_tree = subparsers.add_parser("write-tree", help="snapshot a directory into a tree object")
    p_write_tree.add_argument(
        "path", nargs="?", default=".",
        help="directory to snapshot (default: current directory)"
    )
    p_write_tree.set_defaults(func=cmd_write_tree)

    p_ls_tree = subparsers.add_parser("ls-tree", help="list the contents of a tree object")
    p_ls_tree.add_argument("sha", help="tree object hash")
    p_ls_tree.set_defaults(func=cmd_ls_tree)

    # Phase 2 end
    # Phase 3 begins
    p_commit_tree = subparsers.add_parser("commit-tree", help="create a commit object from a tree")
    p_commit_tree.add_argument("tree", help="tree object hash to commit")
    p_commit_tree.add_argument("-m", "--message", required=True, help="commit message")
    p_commit_tree.add_argument("-p", "-parent", default=None, help="parent commit hash")
    p_commit_tree.set_defaults(func=cmd_commit_tree)

    p_update_ref = subparsers.add_parser("update-ref", help="move the current branch to point at a commit")
    p_update_ref.add_argument("sha", help="commit hash to point at the current branch at")
    p_update_ref.set_defaults(func=cmd_update_ref)

    p_rev_parse = subparsers.add_parser("rev-parse", help="resolve a ref to commit hash")
    p_rev_parse.add_argument("ref", help="ref to resolve, e.g. HEAD")
    p_rev_parse.set_defaults(func=cmd_rev_parse)

    # Phase 3 end
    # Phase 4 begin
    p_add = subparsers.add_parser("add", help="stage files for the next commit")
    p_add.add_argument("files", nargs="+", help="files to stage")
    p_add.set_defaults(func=cmd_add)

    p_commit = subparsers.add_parser("commit", help="record a new commit from staged files")
    p_commit.add_argument("-m", "--message", required=True, help="commit message")
    p_commit.set_defaults(func=cmd_commit)
    # Phase 4 end

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
