"""
Upload compressed JSON snapshots to a HuggingFace private dataset repo.

Requires env vars:
    HF_TOKEN     — HuggingFace write token
    HF_USERNAME  — HuggingFace username (repo owner)
"""

import io
import os

from huggingface_hub import HfApi

REPO_NAME = "japan-bikeshare"
REPO_TYPE = "dataset"


def get_api() -> HfApi:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise EnvironmentError("HF_TOKEN environment variable is not set")
    return HfApi(token=token)


def get_repo_id() -> str:
    username = os.environ.get("HF_USERNAME")
    if not username:
        raise EnvironmentError("HF_USERNAME environment variable is not set")
    return f"{username}/{REPO_NAME}"


def ensure_repo_exists(api: HfApi, repo_id: str):
    try:
        api.repo_info(repo_id=repo_id, repo_type=REPO_TYPE)
    except Exception:
        api.create_repo(repo_id=repo_id, repo_type=REPO_TYPE, private=True)
        print(f"  Created HuggingFace repo: {repo_id}")


def upload(data: bytes, path_in_repo: str):
    api = get_api()
    repo_id = get_repo_id()
    ensure_repo_exists(api, repo_id)

    api.upload_file(
        path_or_fileobj=io.BytesIO(data),
        path_in_repo=path_in_repo,
        repo_id=repo_id,
        repo_type=REPO_TYPE,
    )
