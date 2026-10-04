from app.schemas.pull_request import PullRequestFile
from app.services.diff_processor import (
    build_diff_chunks,
    chunk_patch,
    filter_reviewable_files,
    normalize_patch,
    should_review_file,
)
from app.services.diff_processor import normalize_patch

from app.services.diff_processor import chunk_patch

def test_should_review_normal_source_file():
    assert should_review_file("app/main.py") is True


def test_should_ignore_lock_file():
    assert should_review_file("package-lock.json") is False


def test_should_ignore_binary_file():
    assert should_review_file("assets/logo.png") is False


def test_filter_reviewable_files():
    files = [
        PullRequestFile(
            filename="app/main.py",
            status="modified",
            additions=10,
            deletions=2,
            changes=12,
            patch="some patch",
        ),
        PullRequestFile(
            filename="package-lock.json",
            status="modified",
            additions=100,
            deletions=50,
            changes=150,
            patch="large lockfile patch",
        ),
        PullRequestFile(
            filename="assets/logo.png",
            status="added",
            additions=1,
            deletions=0,
            changes=1,
            patch=None,
        ),
    ]

    reviewable_files = filter_reviewable_files(files)

    assert len(reviewable_files) == 1
    assert reviewable_files[0].filename == "app/main.py"

def test_should_ignore_node_modules_file():
    assert should_review_file("node_modules/package/file.js") is False


def test_should_ignore_build_file():
    assert should_review_file("dist/bundle.js") is False


def test_should_ignore_env_file():
    assert should_review_file(".env") is False

def test_normalize_patch():
    patch = """
@@ -1,3 +1,4 @@

 def hello():
-    print("old")
+    print("new")    
"""

    result = normalize_patch(patch)

    assert result == (
        "@@ -1,3 +1,4 @@\n"
        " def hello():\n"
        '-    print("old")\n'
        '+    print("new")'
    )


def test_normalize_empty_patch():
    assert normalize_patch(None) is None


def test_normalize_whitespace_only_patch():
    assert normalize_patch("   \n   ") is None


def test_chunk_small_patch():
    patch = """@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
"""

    chunks = chunk_patch(
        filename="app/main.py",
        patch=patch,
        max_lines=10,
    )

    assert len(chunks) == 1
    assert chunks[0].filename == "app/main.py"
    assert chunks[0].chunk_index == 0
    assert chunks[0].total_chunks == 1
    assert chunks[0].patch == patch


def test_chunk_large_patch():
    patch = """@@ -1,3 +1,4 @@
 def first():
-    old()
+    new()

@@ -10,3 +11,4 @@
 def second():
-    old()
+    new()

@@ -20,3 +21,4 @@
 def third():
-    old()
+    new()
"""

    chunks = chunk_patch(
        filename="app/main.py",
        patch=patch,
        max_lines=5,
    )

    assert len(chunks) == 3

    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert chunks[2].chunk_index == 2

    assert all(
        chunk.total_chunks == 3
        for chunk in chunks
    )

    assert "@@ -1,3 +1,4 @@" in chunks[0].patch
    assert "@@ -10,3 +11,4 @@" in chunks[1].patch
    assert "@@ -20,3 +21,4 @@" in chunks[2].patch


def test_chunk_empty_patch():
    chunks = chunk_patch(
        filename="app/main.py",
        patch="",
        max_lines=200,
    )

    assert chunks == []

def test_build_diff_chunks():
    files = [
        PullRequestFile(
            filename="app/main.py",
            status="modified",
            additions=5,
            deletions=2,
            changes=7,
            patch="""@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
""",
        ),
        PullRequestFile(
            filename="package-lock.json",
            status="modified",
            additions=100,
            deletions=50,
            changes=150,
            patch="large lockfile patch",
        ),
    ]

    chunks = build_diff_chunks(
        files=files,
        max_lines=200,
    )

    assert len(chunks) == 1
    assert chunks[0].filename == "app/main.py"
    assert chunks[0].chunk_index == 0
    assert chunks[0].total_chunks == 1
    assert "print" in chunks[0].patch