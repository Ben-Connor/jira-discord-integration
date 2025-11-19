from supabase import create_client, Client
import config

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def get_discord_id_by_jira_account_id(jira_account_id: str) -> str:
    """
    Retrieves the Discord ID associated with the given Jira Account ID.
    Returns None if not found.
    """
    try:
        # Try to find by jira_account_id
        response = supabase.table('email_mappings').select('discord_id').eq('jira_account_id', jira_account_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['discord_id']
        
        # Fallback: Try to find by email if the account_id is actually an email (legacy support or if passed accidentally)
        # But strictly we should move to account_id.
        return None
    except Exception as e:
        print(f"Error fetching discord ID for jira account {jira_account_id}: {e}")
        return None

def get_all_tracked_issues() -> dict:
    """
    Retrieves all tracked issues as a dictionary {issue_key: {channel_id, summary}}.
    """
    try:
        response = supabase.table('jira_issues').select('*').execute()
        if response.data:
            return {item['issue_key']: {'channel_id': item['channel_id'], 'summary': item['summary']} for item in response.data}
        return {}
    except Exception as e:
        print(f"Error fetching tracked issues: {e}")
        return {}

def save_created_issue(issue_key: str, channel_id: str, summary: str):
    """
    Saves a new issue to the database to prevent duplicate channel creation.
    """
    try:
        data = {
            'issue_key': issue_key,
            'channel_id': str(channel_id),
            'summary': summary
        }
        supabase.table('jira_issues').insert(data).execute()
    except Exception as e:
        print(f"Error saving issue {issue_key}: {e}")

def delete_issue(issue_key: str):
    """
    Removes an issue from the database.
    """
    try:
        supabase.table('jira_issues').delete().eq('issue_key', issue_key).execute()
    except Exception as e:
        print(f"Error deleting issue {issue_key}: {e}")
