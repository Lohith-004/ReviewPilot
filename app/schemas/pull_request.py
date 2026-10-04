from pydantic import BaseModel


class PullRequestFile(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None = None


class DiffChunk(BaseModel):
    filename: str
    patch: str
    chunk_index: int
    total_chunks: int