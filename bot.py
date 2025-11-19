import discord
from discord.ext import tasks
import config
import jira_client
import db
import asyncio

class JiraBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.guild_id = config.GUILD_ID

    async def setup_hook(self) -> None:
        # Start the background task
        self.check_jira_issues.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=60)  # Check every 60 seconds
    async def check_jira_issues(self):
        print("Checking Jira issues...")
        try:
            # 1. Get active collaborative issues
            issues = jira_client.get_collaborative_active_issues()
            if not issues:
                print("No collaborative issues found.")
                return

            # 2. Get already created issues to avoid duplicates
            created_issue_keys = db.get_created_issues()
            
            guild = self.get_guild(self.guild_id)
            if not guild:
                print(f"Guild with ID {self.guild_id} not found.")
                return

            for issue in issues:
                if issue.key in created_issue_keys:
                    continue
                
                print(f"Processing new issue: {issue.key}")
                await self.create_issue_channel(guild, issue)

        except Exception as e:
            print(f"Error in check_jira_issues loop: {e}")

    async def create_issue_channel(self, guild, issue):
        channel_name = f"{issue.key}-{issue.fields.summary[:20]}".lower().replace(" ", "-")
        # Clean channel name (discord has strict rules)
        channel_name = "".join(c for c in channel_name if c.isalnum() or c in "-_")
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        assignee_mentions = []
        
        # Find discord users for collaborators
        for email in issue.collaborators:
            discord_id = db.get_discord_id_by_email(email)
            if discord_id:
                try:
                    member = await guild.fetch_member(int(discord_id))
                    if member:
                        overwrites[member] = discord.PermissionOverwrite(read_messages=True)
                        assignee_mentions.append(member.mention)
                except Exception as e:
                    print(f"Could not find/add member with ID {discord_id}: {e}")
            else:
                print(f"No Discord ID found for email: {email}")

        try:
            # Create the channel
            channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
            print(f"Created channel {channel.name} for issue {issue.key}")
            
            # Send initial message
            summary = issue.fields.summary
            link = f"{config.JIRA_URL}/browse/{issue.key}"
            mentions_str = " ".join(assignee_mentions)
            
            message = f"**New Collaborative Task**\n**Task:** {issue.key}: {summary}\n**Link:** {link}\n**Assignees:** {mentions_str}\n\nThis channel has been created for you to collaborate on this task."
            await channel.send(message)

            # Save to DB
            db.save_created_issue(issue.key, str(channel.id), summary)

        except Exception as e:
            print(f"Failed to create channel for {issue.key}: {e}")

    @check_jira_issues.before_loop
    async def before_check_jira_issues(self):
        await self.wait_until_ready()

intents = discord.Intents.default()
intents.members = True # Needed to fetch members
intents.guilds = True

client = JiraBot(intents=intents)

def run_bot():
    client.run(config.DISCORD_TOKEN)
