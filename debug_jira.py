import jira_client
import json

def debug_jira_assignee():
    print("Debugging Jira assignee structure...")
    try:
        # Search for the specific issue mentioned in the error or just any active one
        jql = 'status in ("To Do", "In Progress")'
        issues = jira_client.jira.search_issues(jql, maxResults=5, fields="summary,status,subtasks,assignee")
        
        for issue in issues:
            print(f"\nChecking issue: {issue.key}")
            if issue.fields.subtasks:
                for subtask_link in issue.fields.subtasks:
                    try:
                        subtask = jira_client.jira.issue(subtask_link.key, fields="assignee")
                        assignee = subtask.fields.assignee
                        if assignee:
                            print(f"Subtask {subtask.key} Assignee Raw: {assignee.raw}")
                            # Try to access emailAddress
                            try:
                                print(f"Email: {assignee.emailAddress}")
                            except AttributeError:
                                print("Attribute 'emailAddress' not found.")
                            
                            # Try to access accountId
                            try:
                                print(f"AccountId: {assignee.accountId}")
                            except AttributeError:
                                print("Attribute 'accountId' not found.")
                                
                    except Exception as e:
                        print(assignee.raw)
                        print(f"Error fetching subtask {subtask_link.key}: {e}")
            else:
                print("No subtasks.")

    except Exception as e:
        print(f"Jira connection/query failed: {e}")

if __name__ == "__main__":
    debug_jira_assignee()
