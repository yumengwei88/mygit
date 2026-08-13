# mygit

A minimal imitation of Git, built from scratch to understand how Git actually
works.

## Why

After building and deploying two full-stack web apps, I realized they didn't
actually help me understand computer science. While it definitely made me a
better programmer, I wanted to go deeper. 

I chose Git because it's something I work with almost every day without really
understanding what's going on behind the scenes. Turns out, Git is really just
a content-addressable key-value store. Three object types (blobs, trees,
commits) glued together by SHA-1 hashes. This project builds that same process
bit by bit.

## What's implemented so far

**Phase 1 - the object store**
- `mygit init` — creates a `.mygit/` directory with an object store and a
  `main` branch ref, just like `git init`.
- `mygit hash-object [-w] <file>` — hashes a file's contents the same way
  Git does (`"blob <size>\0<content>"`, SHA-1'd), and optionally writes it
  to the object store, compressed with zlib.
- `mygit cat-file -t|-s|-p <sha>` — reads an object back out of the store
  and prints its type, size, or raw content.

The blob hashing is verified against real Git's output (see
`tests/test_phase1.py`) — hashing `"hello world\n"` produces the exact
same SHA-1 that `git hash-object` would.

**Phase 2 — trees (directory snapshots)**
- `mygit write-tree [path]` — recursively snapshots a directory: every
  file becomes a blob, every subdirectory becomes its own nested tree
  object, and the whole thing is tied together into one tree object
  for `path` (default: current directory).
- `mygit ls-tree <sha>` — lists a tree object's contents (mode, type,
  hash, name), the same way `git ls-tree` does.

**Note:** real Git stores each entry's hash as raw 20 binary
bytes to save space. This implementation stores it as plain hex text
instead, so tree objects are directly human-readable via `cat-file -p`.

**Phase 3 — commits and the HEAD/branch chain**
- `mygit commit-tree <tree-sha> -m <message> [-p <parent-sha>]` — creates
  a commit object pointing at a tree snapshot and (optionally) a parent
  commit. Mirrors real Git's plumbing command of the same name — it does
  *not* move any branch pointer on its own.
- `mygit update-ref <commit-sha>` — moves the current branch (whatever
  `HEAD` points to) forward to a given commit.
- `mygit rev-parse HEAD` — resolves `HEAD` down to the actual commit
  hash it currently points at.

**Note:** real Git tracks a separate "author" and "committer" line.
This implementation tracks one identity, but the underlying concept is
the same.

## What's coming next

- **Phase 4**: user-facing porcelain commands — `add`, `commit`, `log`,
  `checkout`
- **Phase 5 (stretch)**: `branch`, basic merges, `diff`

## Setup (VS Code)

1. Open this folder in VS Code (`File > Open Folder...`).
2. Open a terminal (`` Ctrl+` `` / `` Cmd+` ``) and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # on Windows: venv\Scripts\activate
   ```
   VS Code should prompt you to select this as the workspace interpreter —
   accept it (or set it manually via the Python extension's interpreter
   picker in the bottom-right corner).
3. Install the package in editable mode, so `mygit` becomes a real command
   and code changes take effect immediately without reinstalling:
   ```bash
   pip install -e .
   ```
4. Install pytest to run the test suite:
   ```bash
   pip install pytest
   ```

## Usage

```bash
mkdir /tmp/demo && cd /tmp/demo
mygit init
echo "hello world" > greeting.txt
mygit hash-object -w greeting.txt
# -> 3b18e512dba79e4c8300dd08aeb37f8e728b8dad

mygit cat-file -t 3b18e512dba79e4c8300dd08aeb37f8e728b8dad   # blob
mygit cat-file -s 3b18e512dba79e4c8300dd08aeb37f8e728b8dad   # 12
mygit cat-file -p 3b18e512dba79e4c8300dd08aeb37f8e728b8dad   # hello world
```

Peek inside `.mygit/objects/` afterward — you'll see the compressed object
sitting there under a folder named after the first two hash characters,
exactly like real Git.

Snapshotting a whole directory:

```bash
mkdir notes && echo "todo stuff" > notes/todo.txt
TREE_SHA=$(mygit write-tree)
mygit ls-tree $TREE_SHA
```

Building a two-commit history by hand:

```bash
TREE1=$(mygit write-tree)
COMMIT1=$(mygit commit-tree $TREE1 -m "first commit")
mygit update-ref $COMMIT1

echo "more work" > another.txt
TREE2=$(mygit write-tree)
COMMIT2=$(mygit commit-tree $TREE2 -m "second commit" -p $(mygit rev-parse HEAD))
mygit update-ref $COMMIT2
```

## Running tests

```bash
pytest tests/ -v
```

## Project layout

```
mygit-project/
├── mygit/
│   ├── __init__.py
│   ├── cli.py            # argparse command wiring
│   ├── commit.py          # building and reading commit objects
│   ├── objects.py         # hashing, compression, object read/write
│   ├── repository.py      # init + repo discovery + HEAD/branch refs
│   └── tree.py            # building and reading tree objects
├── tests/
│   ├── test_phase1.py
│   ├── test_phase2.py
│   └── test_phase3.py
├── pyproject.toml
└── README.md
```
