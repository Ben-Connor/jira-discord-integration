import config
from supabase import create_client, Client

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def setup_database():
    print("Setting up database...")
    
    # SQL to create tables (using the rpc call if possible, or just assuming they exist if I can't run raw SQL via client easily without admin rights or specific setup).
    # Supabase-py client doesn't support running raw SQL directly for schema creation usually unless using the management API or a stored procedure.
    # However, the user provided the SQL. I'll assume I can't easily run DDL from here without a specific function.
    # But I can try to insert data and see if it fails.
    
    # Actually, I'll try to use the `rpc` method if there's a function, but there probably isn't.
    # I will just try to insert a dummy mapping and see if it works. If the table doesn't exist, it will fail.
    
    print("Checking email_mappings table...")
    try:
        # Try to select
        supabase.table('email_mappings').select("*").limit(1).execute()
        print("email_mappings table exists.")
    except Exception as e:
        print(f"Error accessing email_mappings: {e}")
        print("Please run the provided SQL in your Supabase SQL editor.")
        return

    print("Checking jira_issues table...")
    try:
        supabase.table('jira_issues').select("*").limit(1).execute()
        print("jira_issues table exists.")
    except Exception as e:
        print(f"Error accessing jira_issues: {e}")
        return

    # Insert test mapping
    # I need a discord ID. I'll ask the user for one or use a placeholder.
    # Since I can't ask the user easily in the middle of a task without stopping, I'll insert a placeholder and tell the user to update it.
    # Or I can try to find my own ID if I were a user, but I'm an AI.
    # I'll insert a mapping for the email in .env
    
    email = config.JIRA_EMAIL
    discord_id = "YOUR_DISCORD_ID_HERE" # User needs to update this
    # Placeholder Account ID - User needs to update this too, or I can try to fetch it if I had the client here.
    # But for now, I'll just put a placeholder.
    jira_account_id = "YOUR_JIRA_ACCOUNT_ID_HERE"

    print(f"Inserting/Updating mapping for {email} -> {discord_id} (Account ID: {jira_account_id})")
    try:
        data = {"email": email, "discord_id": discord_id, "jira_account_id": jira_account_id}
        # Upsert
        supabase.table('email_mappings').upsert(data, on_conflict="email").execute()
        print("Mapping inserted. Please update the discord_id and jira_account_id in the database.")
    except Exception as e:
        print(f"Error inserting mapping: {e}")

if __name__ == "__main__":
    setup_database()
