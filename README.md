# issue-to-shortcut-story

Action to automatically create a Shrotcut story whenever an issue is created.

## Workflow example

```yaml
name: "Issue to Shortcut Story"

on: 
  issues:
    types: [opened]

jobs:
  issue-story-linking:
    runs-on: ubuntu-latest
    steps:
      - name: "story-creation"
        uses: yongsub/issue-to-shortcut-story@v0.0.1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          github_repo_name: $REPO_NAME
          github_issue_number: ${{ github.event.issue.number }}
          shortcut_api_token: ${{ secrets.SHORTCUT_API_TOKEN }}
          shortcut_default_user_name: $SHORTCUT_USER_NAME
          shortcut_workflow: $SHORTCUT_WORKFLOW_NAME
          shortcut_group: $SHORTCUT_GROUP_NAME  # optional
          shortcut_project: $SHORTCUT_PROJECT_NAME # optional
          gh_sc_user_map: $ID_MAP # optional
```

## Parameters
- `github_token`
    - Used to request Github API.
    - Recommended to use `${{ secrets.GITHUB_TOKEN }}` in your workflow.
- `github_repo_name`
    - Format: `"{OWNER}/{REPO}"`
- `github_issue_number`
    - Number of the issue just created.
    - Recommended to use `${{ github.event.issue.number }}` in your workflow.
- `shortcut_api_token`
    - Used to request shortcut API.
    - See 
    [Generating a Shortcut API Token](https://help.shortcut.com/hc/en-us/articles/205701199-Shortcut-API-Tokens) and
    [Creating encrypted secrets for a repository](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository)
- `shortcut_default_user_name`
    - Name of a Shortcut user that will become "Requester" of the created story when no Github-Shortcut user map is specified.
- `shortcut_workflow`
    - Shortcut workflow that the story is created.
- `shortcut_group`, optional
    - Shortcut team responsible for the story.
- `shortcut_project`, optional
    - Shortcut project that the story belongs.
- `gh_sc_user_map`, optional
    - Map from Github users to Shortcut users.
        - Format: `"gh_user1:sc_user1, gh_user2:sc_user2"`
            - Comma (,) separates mapping items and colon (:) separates a key-value pair.
            - No space is allowed before and after colon (:).
        - "name", "mention name", and "email address" can be used to specify Shortcut user.
          - Recommended to use "email address" because the others are editable in Shortcut.
    - If specified, the Shortcut user corresponding to the Github user who created the issue will be "Requester" of the story.
    - If not specified, `shortcut_default_user_name` will be "Requester".


