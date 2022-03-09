# issue-to-shortcut-story

Action to automatically create a Shrotcut story whenever an issue is created and synchronize their states whenever the state of the issue is changed.

## Workflow example

```yaml
name: "Issue to Shortcut Story"

on: 
  issues:
    types: [opened, reopened, edited, assigned, unassigned, closed]

jobs:
  issue-story-linking:
    runs-on: ubuntu-latest
    steps:
      - name: "story-creation"
        uses: yongsub/issue-to-shortcut-story@v0.1.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          shortcut_api_token: ${{ secrets.SHORTCUT_API_TOKEN }}
          shortcut_default_user_name: $SHORTCUT_USER_NAME
          shortcut_workflow: $SHORTCUT_WORKFLOW_NAME
          shortcut_team: $SHORTCUT_TEAM_NAME  # optional
          shortcut_project: $SHORTCUT_PROJECT_NAME # optional
          gh_sc_user_map: $ID_MAP  # optional
          gh_action_sc_state_map: $ACTION_STATE_MAP  # optional
```

## Parameters
- `github_token`
    - Used to request Github API.
    - Recommended to use `${{ secrets.GITHUB_TOKEN }}` in your workflow.
- `shortcut_api_token`
    - Used to request shortcut API.
    - See 
    [Generating a Shortcut API Token](https://help.shortcut.com/hc/en-us/articles/205701199-Shortcut-API-Tokens) and
    [Creating encrypted secrets for a repository](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository)
- `shortcut_default_user_name`
    - Name of a Shortcut user that will become "Requester" of the created story when no Github-Shortcut user map is specified.
- `shortcut_workflow`
    - Shortcut workflow that the story is created.
- `shortcut_team`, optional
    - Shortcut team responsible for the story.
- `shortcut_project`, optional
    - Shortcut project that the story belongs.
- `gh_sc_user_map`, optional
    - Map from Github users to Shortcut users in JSON.
        - Example:
            ```
            '{"gh_user1": "sc_user1", "gh_user2": "sc_user2"}'
            ```
        - "name", "mention name", and "email address" can be used to specify Shortcut user.
    - If specified, the Shortcut user corresponding to the Github user who created the issue will be "Requester" of the story.
    - If not specified, `shortcut_default_user_name` will be "Requester".
- `gh_action_sc_state_map`, optional
    - Map from action triggers to Shortcut workflow states in JSON.
        - Example:
            ```
            '{"opened": "Unscheduled", "closed": "Completed"}'
            ``` 
    - For the following event types, default values will be used if not specified.
        - "opened": first state of the workflow specified above
        - "reopened": the same as "opened"
        - "closed": last state of the workflow specified above
        - For the others, the current workflow state remains unchanged.



