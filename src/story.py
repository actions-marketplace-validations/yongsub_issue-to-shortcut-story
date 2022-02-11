
from typing import Dict, List, Optional
from pydantic import BaseModel


class StorySpec(BaseModel):
    # required
    name: str
    description: Optional[str] = None
    requested_by_id: Optional[str] = None
    story_type: str = "feature"

    # recommended
    owner_ids: List[str] = []
    group_id: Optional[str] = None
    workflow_state_id: Optional[int] = None
    project_id: Optional[int] = None

    # optional
    labels: Optional[Dict] = None
    deadline: Optional[str] = None
    estimate: Optional[int] = None
    epic_id: Optional[int] = None
    iteration_id: Optional[int] = None

    # automatic
    created_at: Optional[str] = None

    # I don't know
    archived: bool = False
    completed_at_override: Optional[str] = ""
    external_id: str = ""
    started_at_override: Optional[str] = None
    story_template_id: Optional[str] = None
    updated_at: Optional[str] = None

    comments: List[Dict] = []
    tasks: List[Dict] = []
    story_links: List[Dict] = []

    external_links: List[str] = []
    follower_ids: List[str] = []

    file_ids: List[int] = []
    linked_file_ids: List[int] = []
