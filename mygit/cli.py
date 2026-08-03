"""Command-line interface for mygit."""

import argparse
import sys

from . import objects
from . import repository
from . import tree


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

# Phase 2
def cmd_write_tree(args):
    try:
        repo = repository.find_repo()
    except repository.RepositoryError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    sha = tree.write_tree(repo, args.path)
    print(sha)

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

    # Phase 2 end

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
