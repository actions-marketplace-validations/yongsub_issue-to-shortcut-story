import arrow
import os
import requests
from story import Story


class Shortcut:
    SHORTCUT_API_BASE_URL = "https://api.app.shortcut.com/api/v3"

    SHORTCUT_API_HEADERS = {
        "Content-Type": "application/json",
        "Shortcut-Token": None,
    }

    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.environ["SHORTCUT_API_TOKEN"]

        self._api_key = api_key

    def get_api_headers(self):
        headers = self.SHORTCUT_API_HEADERS
        headers["Shortcut-Token"] = self._api_key
        return headers

    def get(self, name):
        shortcut_api_headers = self.get_api_headers()

        resp = requests.get(
            url=f"{self.SHORTCUT_API_BASE_URL}/{name}",
            headers=shortcut_api_headers,
        )

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            print(f"Getting {name} failed.")
            print(ex)
            print(resp.json())
            exit(1)

        return resp

    def get_member(
        self,
        member_name,
        match_keys=["name", "mention_name", "email_address"],
    ):
        obj = self.get("members")

        for member in obj.json():
            profile = member["profile"]

            match_values = [profile[key] for key in match_keys]

            if member_name in match_values:
                return member

        return None

    def get_member_id(
        self,
        member_name,
        match_keys=["name", "mention_name", "email_address"],
    ):
        member = self.get_member(member_name, match_keys)

        if member is None:
            return None
        else:
            return member["id"]

    def get_workflow(self, workflow_name):
        obj = self.get("workflows")

        found = [item for item in obj.json() if item["name"] == workflow_name]

        if len(found) > 0:
            return found[0]
        else:
            return None

    def get_my_id(self):
        obj = self.get("member")

        return obj.json()["id"]

    def get_group_id(self, group_name):
        obj = self.get("groups")

        group_ids = [item for item in obj.json() if item["name"] == group_name]

        if len(group_ids) > 0:
            return group_ids[0]["id"]
        else:
            return None

    def get_project_id(self, project_name):
        obj = self.get("projects")

        projects = [item for item in obj.json() if item["name"] == project_name]

        if len(projects) > 0:
            return projects[0]["id"]
        else:
            return None

    def create_story(self, story: Story):
        if story.requested_by_id is None:
            my_id = self.get_my_id()
            story.requested_by_id = my_id

        if story.created_at is None:
            curr = arrow.now().isoformat()
            story.created_at = curr
            story.completed_at_override = curr
            story.started_at_override = curr
            story.updated_at = curr

        url = self.SHORTCUT_API_BASE_URL + "/stories"
        headers = self.SHORTCUT_API_HEADERS

        response = requests.post(url=url, headers=headers, data=story.json())

        return response
