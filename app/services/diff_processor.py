from app.schemas.pull_request import PullRequestFile

from app.schemas.pull_request import DiffChunk


IGNORED_FILE_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    ".env",
}

IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
}

IGNORED_PATH_PARTS = {
    "node_modules/",
    "dist/",
    "build/",
    "__pycache__/",
    ".pytest_cache/",
    "coverage/",
}


def should_review_file(filename: str) -> bool:
    """
    Decide whether a changed file should be reviewed by the AI.
    """

    filename_lower = filename.lower()

    if filename_lower in {
        name.lower()
        for name in IGNORED_FILE_NAMES
    }:
        return False

    for path_part in IGNORED_PATH_PARTS:
        if path_part in filename_lower:
            return False

    for extension in IGNORED_EXTENSIONS:
        if filename_lower.endswith(extension):
            return False

    return True


def filter_reviewable_files(
    files: list[PullRequestFile],
) -> list[PullRequestFile]:
    """
    Keep only files that are relevant for code review.
    """

    return [
        file
        for file in files
        if should_review_file(file.filename)
    ]

def normalize_patch(patch: str | None) -> str | None:
    """
    Normalize a GitHub patch before sending it for review.
    """

    if not patch:
        return None

    lines = patch.splitlines()

    normalized_lines = [
        line.rstrip()
        for line in lines
        if line.strip()
    ]

    if not normalized_lines:
        return None

    return "\n".join(normalized_lines)


def chunk_patch(
    filename: str,
    patch: str,
    max_lines: int = 200,
) -> list[DiffChunk]:
    """
    Split a large diff patch into manageable chunks.

    Chunks are split at Git diff hunk headers whenever possible.
    """

    if not patch.strip():
        return []

    lines = patch.splitlines()

    if len(lines) <= max_lines:
        return [
            DiffChunk(
                filename=filename,
                patch=patch,
                chunk_index=0,
                total_chunks=1,
            )
        ]

    sections: list[list[str]] = []
    current_section: list[str] = []

    for line in lines:
        if line.startswith("@@") and current_section:
            sections.append(current_section)
            current_section = []

        current_section.append(line)

    if current_section:
        sections.append(current_section)

    chunks: list[str] = []
    current_chunk: list[str] = []

    for section in sections:
        if (
            current_chunk
            and len(current_chunk) + len(section) > max_lines
        ):
            chunks.append("\n".join(current_chunk))
            current_chunk = []

        current_chunk.extend(section)

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    total_chunks = len(chunks)

    return [
        DiffChunk(
            filename=filename,
            patch=chunk,
            chunk_index=index,
            total_chunks=total_chunks,
        )
        for index, chunk in enumerate(chunks)
    ]

def build_diff_chunks(
    files: list[PullRequestFile],
    max_lines: int = 200,
) -> list[DiffChunk]:
    """
    Build reviewable diff chunks from GitHub PR files.

    Pipeline:
    1. Filter ignored files.
    2. Normalize patches.
    3. Split large patches into chunks.
    """

    reviewable_files = filter_reviewable_files(files)

    chunks: list[DiffChunk] = []

    for file in reviewable_files:
        normalized_patch = normalize_patch(file.patch)

        if normalized_patch is None:
            continue

        file_chunks = chunk_patch(
            filename=file.filename,
            patch=normalized_patch,
            max_lines=max_lines,
        )

        chunks.extend(file_chunks)

    return chunks