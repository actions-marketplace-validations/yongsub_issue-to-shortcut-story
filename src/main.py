import re
import json
from typing import Dict, Optional
from pydantic import BaseSettings, BaseModel, Field
from github import Github
from shortcut import Shortcut


class StoryNotFound(Exception):
    pass


class Environ(BaseSettings):
    """
    Env variables
    """

    """Provided by Github """
    gh_event_name: str = Field(env="GITHUB_EVENT_NAME")
    gh_event_path: str = Field(env="GITHUB_EVENT_PATH")

    """Provided by User"""
    gh_token: str = Field(env="INPUT_GITHUB_TOKEN")
    sc_api_token: str = Field(env="INPUT_SHORTCUT_API_TOKEN")
    sc_default_user_name: str = Field(env="INPUT_SHORTCUT_DEFAULT_USER_NAME")
    sc_workflow: str = Field(env="INPUT_SHORTCUT_WORKFLOW")
    sc_team: Optional[str] = Field(env="INPUT_SHORTCUT_TEAM")
    sc_project: Optional[str] = Field(env="INPUT_SHORTCUT_PROJECT")
    gh_sc_user_map: Optional[Dict[str, str]] = Field(env="INPUT_GH_SC_USER_MAP")
    gh_action_sc_state_map: Optional[Dict[str, str]] = Field(env="INPUT_GH_ACTION_SC_STATE_MAP")


class Setting(BaseModel):
    environ: Environ
    gh_event_action: str
    gh_issue_number: int
    gh_repo_name: str
    sc_workflow_state_id: int
    sc_group_id: Optional[str]
    sc_project_id: Optional[int]
    sc_default_user_id: str
    gh_sc_id_map: Dict[str, str]
    gh_action_sc_state_id_map: Dict[str, str]


def make_story_spec(issue, setting):
    gh_user_name = issue.user.login
    requested_by_id = setting.gh_sc_id_map.get(gh_user_name, setting.sc_default_user_id)

    issue_url = issue.html_url
    story_body = f"Automatically created by [this issue]({issue_url})"

    story_spec = {
        "name": issue.title,
        "description": story_body,
        "requested_by_id": requested_by_id,
        "group_id": setting.sc_group_id,
        "workflow_state_id": setting.sc_workflow_state_id,
        "project_id": setting.sc_project_id,
    }

    return story_spec


def make_story_link_text(story):
    story_id = story["id"]
    story_url = story["app_url"]

    story_hyperlink = f"[sc-{story_id}]({story_url})"
    issue_comment = f":link: Linked to [{story_hyperlink}] (automatically added by issue-to-shortcut-story)"

    return issue_comment


def get_linked_story_id(issue):
    comments = issue.get_comments()

    story_id = None

    for comment in comments:
        patterns = re.findall(r"\[sc-[1-9][0-9]*\]", comment.body)

        if len(patterns) > 0:
            story_id = int(patterns[0][4:-1])
            break

    if story_id is None:
        raise Exception("Any associated story cannot be found in `issue`.")

    return story_id


def make_story_meta(issue, setting):
    story_owner_ids = []
    for gh_user in issue.assignees:
        gh_name = gh_user.login
        sc_id = setting.gh_sc_id_map.get(gh_name, setting.sc_default_user_id)

        if sc_id not in story_owner_ids:
            story_owner_ids.append(sc_id)

    gh_action_sc_state_id_map = setting.gh_action_sc_state_id_map
    workflow_state_id = gh_action_sc_state_id_map.get(setting.gh_event_action, None)

    story_meta = {
        "name": "[Github Issue] " + issue.title,
        "owner_ids": story_owner_ids,
    }

    if workflow_state_id is not None:
        story_meta["workflow_state_id"] = workflow_state_id

    return story_meta


def make_setting(environ, shortcut):
    with open(environ.gh_event_path, "r") as f:
        event = json.load(f)

    gh_event_action = event["action"]
    gh_issue_number = event["issue"]["number"]
    gh_repo_name = event["repository"]["full_name"]

    sc_workflow = shortcut.get_workflow(environ.sc_workflow)

    assert sc_workflow is not None

    sc_workflow_state_id = sc_workflow["states"][0]["id"]
    sc_group_id = shortcut.get_group_id(environ.sc_team)
    sc_project_id = shortcut.get_project_id(environ.sc_project)
    sc_default_user_id = shortcut.get_member_id(environ.sc_default_user_name)

    assert sc_default_user_id is not None

    if environ.gh_sc_user_map is None:
        gh_sc_id_map = {}
    else:
        gh_sc_id_map = {
            gh_user_name: shortcut.get_member_id(sc_user_name)
            for gh_user_name, sc_user_name in environ.gh_sc_user_map.items()
        }

        gh_sc_id_map = {k: v for k, v in gh_sc_id_map.items() if v is not None}

    if environ.gh_action_sc_state_map is None:
        gh_action_sc_state_id_map = {}
    else:
        workflow_state_name_id_map = {
            state["name"]: state["id"]
            for state in sc_workflow["states"]
        }

        gh_action_sc_state_id_map = {
            gh_action: workflow_state_name_id_map[sc_state]
            for gh_action, sc_state in environ.gh_action_sc_state_map.items()
        }

    gh_action_sc_state_id_map.setdefault("opened", sc_workflow["states"][0]["id"])
    gh_action_sc_state_id_map.setdefault("reopened", sc_workflow["states"][0]["id"])
    gh_action_sc_state_id_map.setdefault("closed", sc_workflow["states"][-1]["id"])

    setting = Setting(
        environ=environ,
        gh_event_action=gh_event_action,
        gh_issue_number=gh_issue_number,
        gh_repo_name=gh_repo_name,
        sc_workflow_state_id=sc_workflow_state_id,
        sc_group_id=sc_group_id,
        sc_project_id=sc_project_id,
        sc_default_user_id=sc_default_user_id,
        gh_sc_id_map=gh_sc_id_map,
        gh_action_sc_state_id_map=gh_action_sc_state_id_map,
    )

    return setting


def main():
    environ = Environ()

    if environ.gh_event_name != "issues":
        print("event_name is not issue. Action issue-to-shortcut-story does nothing.")
        exit(0)

    print(environ.dict())

    github = Github(environ.gh_token)
    shortcut = Shortcut(environ.sc_api_token)

    setting = make_setting(environ, shortcut)

    issue = (
        github
        .get_repo(setting.gh_repo_name)
        .get_issue(setting.gh_issue_number)
    )

    if setting.gh_event_action == "opened":
        story_spec = make_story_spec(issue, setting)
        story = shortcut.create_story(story_spec)

        print(">>> Story is created.")
        print(f"  - id: {story['id']}.")
        print(f"  - title: {story['name']}.")

        comment = make_story_link_text(story)
        issue.create_comment(comment)

    try:
        story_id = get_linked_story_id(issue)
        story = shortcut.get_story(story_id)

        story_meta = make_story_meta(issue, setting)
        shortcut.update_story(story_id, story_meta)

        print(">>> Storyy is updated.")
        for k, v in story_meta.items():
            print(f"  - {k}: {v}")
    except StoryNotFound:
        print(f">>> Any linked story cannot be found in the issue ({issue.number})")
    except Exception:
        print(">>> Action failed.")
        raise


if __name__ == "__main__":
    main()
