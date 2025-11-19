import jira_client

def test_jira():
    print("Testing Jira connection...")
    try:
        user = jira_client.jira.myself()
        print(f"Connected to Jira as: {user['displayName']}")
        
        print("Querying for issues...")
        issues = jira_client.get_collaborative_active_issues()
        print(f"Found {len(issues)} collaborative active issues.")
        for issue in issues:
            print(f" - {issue.key}: {issue.fields.summary}")
            
    except Exception as e:
        print(f"Jira connection failed: {e}")

if __name__ == "__main__":
    test_jira()
