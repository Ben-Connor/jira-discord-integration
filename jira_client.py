from jira import JIRA
import config

# Initialize Jira client
jira = JIRA(
    server=config.JIRA_URL,
    basic_auth=(config.JIRA_EMAIL, config.JIRA_API_TOKEN)
)

def get_collaborative_active_issues():
    """
    Queries active Jira tasks (Todo, In Progress) and returns those
    that have subtasks with more than 1 unique assignee.
    """
    print("Querying Jira for active issues...")
    # JQL to get active issues. Adjust status names if needed.
    jql = 'status in ("To Do", "In Progress")'
    
    try:
        issues = jira.search_issues(jql, maxResults=100, fields="summary,status,subtasks,assignee")
        collaborative_issues = []

        for issue in issues:
            # We need to fetch the full issue to get subtask details (assignees)
            # The search result 'subtasks' field only contains basic info.
            # Optimization: Only fetch full details if there are subtasks.
            if not issue.fields.subtasks:
                continue

            unique_assignees = set()
            
            # Iterate through subtasks
            for subtask_link in issue.fields.subtasks:
                try:
                    subtask = jira.issue(subtask_link.key, fields="assignee")
                    if subtask.fields.assignee:
                        unique_assignees.add(subtask.fields.assignee.emailAddress)
                except Exception as e:
                    print(f"Error fetching subtask {subtask_link.key}: {e}")

            # Check if more than 1 unique assignee
            if len(unique_assignees) > 1:
                # Attach the assignees to the issue object for easier access later
                issue.collaborators = list(unique_assignees)
                collaborative_issues.append(issue)
                print(f"Found collaborative issue: {issue.key} with assignees: {unique_assignees}")

        return collaborative_issues

    except Exception as e:
        print(f"Error querying Jira: {e}")
        return []
