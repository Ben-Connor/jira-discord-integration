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
        print("Syncing Jira issues...")
        try:
            # 1. Get active collaborative issues from Jira
            active_issues = jira_client.get_collaborative_active_issues()
            active_issue_keys = {issue.key for issue in active_issues}
            active_issues_map = {issue.key: issue for issue in active_issues}

            # 2. Get tracked issues from DB
            tracked_issues = db.get_all_tracked_issues() # Returns {key: {channel_id, summary}}
            tracked_issue_keys = set(tracked_issues.keys())
            
            guild = self.get_guild(self.guild_id)
            if not guild:
                print(f"Guild with ID {self.guild_id} not found.")
                print("Available Guilds:")
                for g in self.guilds:
                    print(f" - {g.name} (ID: {g.id})")
                return

            # 3. Handle New Issues
            new_issues = active_issue_keys - tracked_issue_keys
            for key in new_issues:
                print(f"Found new issue: {key}")
                await self.create_issue_channel(guild, active_issues_map[key])

            # 4. Handle Gone Issues (Done or no longer collaborative)
            gone_issues = tracked_issue_keys - active_issue_keys
            for key in gone_issues:
                print(f"Issue {key} is no longer active/collaborative. Cleaning up...")
                channel_id = tracked_issues[key]['channel_id']
                await self.delete_issue_channel(guild, channel_id, key)

            # 5. Handle Updated Issues (Check for new assignees)
            existing_issues = active_issue_keys.intersection(tracked_issue_keys)
            for key in existing_issues:
                await self.sync_issue_assignees(guild, active_issues_map[key], tracked_issues[key]['channel_id'])

        except Exception as e:
            print(f"Error in check_jira_issues loop: {e}")

    async def delete_issue_channel(self, guild, channel_id, issue_key):
        try:
            channel = guild.get_channel(int(channel_id))
            if channel:
                await channel.delete(reason=f"Issue {issue_key} no longer active/collaborative")
                print(f"Deleted channel for {issue_key}")
            else:
                print(f"Channel {channel_id} for {issue_key} not found (already deleted?)")
            
            # Remove from DB
            db.delete_issue(issue_key)
        except Exception as e:
            print(f"Error deleting channel for {issue_key}: {e}")

    async def sync_issue_assignees(self, guild, issue, channel_id):
        try:
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return

            current_members = channel.members
            current_member_ids = {member.id for member in current_members}
            
            for email in issue.collaborators:
                discord_id = db.get_discord_id_by_jira_account_id(email) # issue.collaborators now holds accountIds
                if discord_id and int(discord_id) not in current_member_ids:
                    try:
                        member = await guild.fetch_member(int(discord_id))
                        if member:
                            await channel.set_permissions(member, read_messages=True)
                            await channel.send(f"Welcome {member.mention}! You have been added to this task.")
                            print(f"Added {member.name} to {issue.key}")
                    except Exception as e:
                        print(f"Error adding member {discord_id} to {issue.key}: {e}")
        except Exception as e:
            print(f"Error syncing assignees for {issue.key}: {e}")

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
        for account_id in issue.collaborators:
            discord_id = db.get_discord_id_by_jira_account_id(account_id)
            if discord_id:
                try:
                    member = await guild.fetch_member(int(discord_id))
                    if member:
                        overwrites[member] = discord.PermissionOverwrite(read_messages=True)
                        assignee_mentions.append(member.mention)
                except Exception as e:
                    print(f"Could not find/add member with ID {discord_id}: {e}")
            else:
                print(f"No Discord ID found for Jira Account ID: {account_id}")

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
