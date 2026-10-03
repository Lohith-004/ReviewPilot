from pydantic import BaseModel


class PullRequestRepository(BaseModel):
    name: str
    full_name: str


class PullRequestUser(BaseModel):
    login: str


class PullRequestRef(BaseModel):
    sha: str


class PullRequestData(BaseModel):
    number: int
    title: str
    user: PullRequestUser
    head: PullRequestRef
    base: PullRequestRef

class GitHubInstallation(BaseModel):
    id: int


class PullRequestEvent(BaseModel):
    action: str
    number: int
    installation: GitHubInstallation
    pull_request: PullRequestData
    repository: PullRequestRepository