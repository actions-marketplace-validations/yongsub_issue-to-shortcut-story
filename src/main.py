import sys
import requests
from pprint import pprint
from typing import Optional
from pydantic import BaseSettings, Field
from shortcut import Shortcut
from story import Story


class Setting(BaseSettings):
    """
    Env variables
    """

    gh_token: str = Field(env="INPUT_GITHUB_TOKEN")
    gh_repo_name: str = Field(env="INPUT_GITHUB_REPO_NAME")
    gh_issue_num: str = Field(env="INPUT_GITHUB_ISSUE_NUMBER")
    sc_api_token: str = Field(env="INPUT_SHORTCUT_API_TOKEN")
    sc_default_user_name: str = Field(env="INPUT_SHORTCUT_DEFAULT_USER_NAME")
    sc_workflow: str = Field(env="INPUT_SHORTCUT_WORKFLOW")
    sc_team: Optional[str] = Field(env="INPUT_SHORTCUT_TEAM")
    sc_project: Optional[str] = Field(env="INPUT_SHORTCUT_PROJECT")
    gh_sc_user_map: Optional[str] = Field(env="INPUT_GH_SC_USER_MAP")


def determine_workflow_state(sc, workflow_name, issue_labels):
    workflow = sc.get_workflow(workflow_name)

    if workflow is None:
        raise ValueError(f"Workflow {workflow_name} does not exist.")

    match_states = [wf_state for wf_state in workflow["states"] if wf_state["name"] in issue_labels]

    if len(match_states) > 0:
        target_state = match_states[0]
    else:
        target_state = workflow["states"][0]

    return target_state


def get_issue(gh_issue_num, gh_repo_name, gh_token):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {gh_token}",
    }
    url = f"https://api.github.com/repos/{gh_repo_name}/issues/{gh_issue_num}"

    print(f">>> Issue {gh_issue_num} ({type(gh_issue_num)}) is created")
    print(f">>>   - Request {url}")

    res = requests.get(url=url, headers=headers)

    try:
        res.raise_for_status()

        html_url = res.json()["html_url"]

    except requests.exceptions.HTTPError as ex:
        print(ex)
        # if not 200
        print(res.status_code)
        print(res.json())
        print("github token or github relevant inputs are invalid")
        sys.exit(1)

    return res.json()


def parse_to_user_map(gh_sc_user_map_str):
    try:
        user_map = dict([
            pair.strip().split(":")
            for pair in gh_sc_user_map_str.split(",")
        ])
    except Exception:
        print(">>> Parsing gh_sc_user_map failed.")
        user_map = None

    return user_map


def determine_requested_by_id(sc, gh_user_name, gh_sc_user_map_str, sc_default_user_name):
    sc_default_user_id = sc.get_member_id(sc_default_user_name)

    assert sc_default_user_id is not None

    gh_sc_user_map = parse_to_user_map(gh_sc_user_map_str)

    if gh_sc_user_map is None:
        print(f">>> github-shortcut user map is not given ({gh_sc_user_map_str}).")
        print(f">>>   - Default shortcut user ({sc_default_user_name}) is used for requested by of a story.")
        requested_by_id = sc_default_user_id

    elif gh_user_name in gh_sc_user_map:
        sc_user_name = gh_sc_user_map[gh_user_name]
        sc_user_id = sc.get_member_id(sc_user_name)

        if sc_user_id is None:
            print(f">>> Shortcut user {sc_user_name} cannot be found.")
            print(f">>>   - Default Shortcut user ({sc_default_user_name}) will be used to set `requested_by_id`.")
            requested_by_id = sc_default_user_id
        else:
            print(f">>> Shortcut user {sc_user_name} is found.")
            requested_by_id = sc_user_id

    else:
        print(f">>> Github user {gh_user_name} has no associated Shortcut user.")
        print(f">>>   - Default Shortcut user ({sc_default_user_name}) will be used to set `requested_by_id`.")
        requested_by_id = sc_default_user_id

    return requested_by_id


if __name__ == "__main__":
    setting = Setting()

    print(setting)

    sc = Shortcut(setting.sc_api_token)

    issue = get_issue(setting.gh_issue_num, setting.gh_repo_name, setting.gh_token)
    issue_labels = [lb["name"] for lb in issue["labels"]]

    workflow_state = determine_workflow_state(sc, setting.sc_workflow, issue_labels)
    workflow_state_id = workflow_state["id"]

    gh_user_name = issue["user"]["login"]
    requested_by_id = determine_requested_by_id(
        sc,
        gh_user_name,
        setting.gh_sc_user_map,
        setting.sc_default_user_name,
    )

    group_id = sc.get_group_id(setting.sc_team)
    project_id = sc.get_project_id(setting.sc_project)

    issue_url = f"https://github.com/{setting.gh_repo_name}/issues/{setting.gh_issue_num}"
    story_body = f"Automatically created by [this issue]({issue_url})"

    story = Story(
        name=issue["title"],
        description=story_body,
        requested_by_id=requested_by_id,
        group_id=group_id,
        workflow_state_id=workflow_state_id,
        project_id=project_id,
    )

    print(story)

    r = sc.create_story(story)

    try:
        r.raise_for_status()

        story_id = r.json()["id"]

        print(f">>> Story {story_id} is created.")

    except requests.exceptions.HTTPError as ex:
        print(ex)
        # if not 200
        print(r.status_code)
        print(r.json())
        print("Story creation failed.")
        sys.exit(1)
