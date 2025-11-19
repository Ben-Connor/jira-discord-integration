from supabase import create_client, Client
import config

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def get_discord_id_by_email(email: str) -> str:
    """
    Retrieves the Discord ID associated with the given email.
    Returns None if not found.
    """
    try:
        response = supabase.table('email_mappings').select('discord_id').eq('email', email).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['discord_id']
        return None
    except Exception as e:
        print(f"Error fetching discord ID for email {email}: {e}")
        return None

def get_created_issues() -> list[str]:
    """
    Retrieves a list of issue keys that have already been processed/created.
    """
    try:
        response = supabase.table('jira_issues').select('issue_key').execute()
        if response.data:
            return [item['issue_key'] for item in response.data]
        return []
    except Exception as e:
        print(f"Error fetching created issues: {e}")
        return []

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
