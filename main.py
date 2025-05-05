import discord
import time
import logging
import json
import os
from webserver import trigger_refresh
from discord.ext import commands
from dotenv import load_dotenv, dotenv_values


'''Setup'''
# Get environment information from env file. Use Discord Developer mode for Guild ID or App Token.
load_dotenv()
MY_GUILD = discord.Object(id=int(os.getenv("GUILD_ID")))
TOKEN = os.getenv("DISCORD_TOKEN")
# Handle intents
intents = discord.Intents.default()
intents.message_content = True
# Handle logging
logger = logging.getLogger("discord")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)  # Set the logging level directly on the logger
# Set up data structures for player stats
stats = {}
POINTS_PER_GAME_TYPE = {
    3: [2, 1, 0],
    4: [6, 2, 0, -2]
}
DEFAULT_PFP = "https://cdn.prod.website-files.com/6257adef93867e50d84d30e2/66e3d8014ea898f3a4b2156c_Symbol.svg"
MIN_PLAYER_CT = 3
MAX_PLAYER_CT = 4
# Setup bot
bot = commands.Bot(command_prefix = commands.when_mentioned, intents = intents)

''' Stat Saving and Handling'''
def save_stats():
    try:
        with open('player_stats.json', 'w') as f:
            json.dump(stats, f)
    except IOError as e:
        logger.error(f"Failed to save stats: {e}")
def load_stats():
    global stats
    try:
        with open('player_stats.json', 'r') as f:
            stats = json.load(f)
    except FileNotFoundError:
        stats = {}
    except json.JSONDecodeError:
        logger.error("Error decoding JSON data from player_stats.json.")
        stats = {}
    except IOError as e:
        logger.error(f"Error loading stats file: {e}")
        stats = {}
    return stats

def add_player(player):
    if player.id not in stats:
        stats[player.id] = {
            "nickname": player.display_name or player.name,
            "avatar_url": player.avatar.url if player.avatar else DEFAULT_PFP,
            "3": {"points": 0, "games_played": 0},
            "4": {"points": 0, "games_played": 0}
    }
    logger.debug(f"add_played - added {player.name}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    
    try:
        synced = await bot.tree.sync(guild=MY_GUILD)
        print(f"Synced {len(synced)} command(s) to the guild {MY_GUILD.id}.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

''' Slash Command - Add Game '''
@bot.tree.command(name="addgame", description="Add a game result for 3 or 4 players. List users in order of ranking.", guild=MY_GUILD)
async def addgame(
    interaction: discord.Interaction,
    p1: discord.Member,
    p2: discord.Member,
    p3: discord.Member,
    p4: discord.Member = None
):
    load_stats()
    # validate player count and uniqueness
    players = [player for player in [p1, p2, p3, p4] if player is not None]
    
    # Check for duplicate users
    if len(set(player.id for player in players)) < MIN_PLAYER_CT or len(set(player.id for player in players)) > MAX_PLAYER_CT:
        await interaction.response.send_message(
            f"Only {MIN_PLAYER_CT} to {MAX_PLAYER_CT} unique players allowed.",
            ephemeral=True
        )
        logger.debug("addgame - incorrect player count")
        return

    player_count = len(players)

    ppgt = POINTS_PER_GAME_TYPE[player_count]
    
    for idx, player in enumerate(players):

        add_player(player=player) # if player is not already present in stats

        # Assign points based on position
        stats[player.id][str(player_count)]['points'] += ppgt[idx]
        stats[player.id][str(player_count)]['games_played'] += 1

    save_stats()
    logger.debug("/addgame - saved stats")
    trigger_refresh()
    logger.debug("/addgame - trigger refresh")

    await interaction.response.send_message(
        f"Game recorded for {player_count} players. Use /leaderboard to see updated leaderboard."
    )
    
        
''' Slash Command - Edit Player Point Total per Game Type'''
@bot.tree.command(name="edit", description="Edit a player's point total.", guild=MY_GUILD)
async def edit(
    interaction: discord.Interaction, 
    player: discord.Member,
    player_count: int,
    points: int,
    game_count: int
):
    await interaction.response.defer(thinking=True)  # Defer immediately

    if player_count < MIN_PLAYER_CT or player_count > MAX_PLAYER_CT:
        await interaction.followup.send(
            f"Player count must be between {MIN_PLAYER_CT} and {MAX_PLAYER_CT}.",
            ephemeral=True
        )
        return

    load_stats()
    add_player(player=player)  # Add if not present
    stats[player.id][str(player_count)]['points'] = points
    stats[player.id][str(player_count)]['games_played'] = game_count
    save_stats()

    try:
        trigger_refresh()
        logger.debug("/edit - trigger refresh")
    except Exception as e:
        logger.exception(f"Failed to trigger refresh: {e}")

    await interaction.followup.send(
        f"{player.mention}'s score for {player_count}-player games has been updated to {points} points in {game_count} games played."
    )


''' Format Player Stats for Leaderboard '''
async def send_player_stats(interaction: discord.Interaction, stats: dict, sort_by: str = "total_gp"):
    embed = discord.Embed(title="Leaderboard")
    
    # Initialize max trackers
    max_3p_pts = max_3p_ppg = max_4p_pts = max_4p_ppg = max_total_gp = 0
    rows = []

    # First pass: gather stats and track max values
    for player_id, modes in stats.items():
        p3 = modes.get("3", {})
        p3_pts = p3.get("points", 0)
        p3_gp = p3.get("games_played", 0)
        p3_ppg = round(p3_pts / p3_gp, 2) if p3_gp else 0

        p4 = modes.get("4", {})
        p4_pts = p4.get("points", 0)
        p4_gp = p4.get("games_played", 0)
        p4_ppg = round(p4_pts / p4_gp, 2) if p4_gp else 0

        total_gp = p3_gp + p4_gp

        max_3p_pts = max(max_3p_pts, p3_pts)
        max_3p_ppg = max(max_3p_ppg, p3_ppg)
        max_4p_pts = max(max_4p_pts, p4_pts)
        max_4p_ppg = max(max_4p_ppg, p4_ppg)
        max_total_gp = max(max_total_gp, total_gp)

        rows.append({
            "player_id": player_id,
            "p3_pts": p3_pts,
            "p3_ppg": p3_ppg if p3_gp else "-",
            "p3_gp": p3_gp,
            "p4_pts": p4_pts,
            "p4_ppg": p4_ppg if p4_gp else "-",
            "p4_gp": p4_gp,
            "total_gp": total_gp
        })

    # Second pass: format embed fields
    for r in rows:
        try:
            member = await interaction.guild.fetch_member(int(r['player_id']))
            mention = f"**{member.mention}**"
        except discord.NotFound:
            mention = f"Unknown:{r['player_id']}"

        def with_crown(val, max_val, exclude=False):
            return f"{val} 👑" if val == max_val and not exclude and val != "-" else str(val)

        p3_pts = with_crown(r['p3_pts'], max_3p_pts)
        p3_ppg = with_crown(r['p3_ppg'], max_3p_ppg)
        p3_gp  = str(r['p3_gp'])  # No crown on games played

        p4_pts = with_crown(r['p4_pts'], max_4p_pts)
        p4_ppg = with_crown(r['p4_ppg'], max_4p_ppg)
        p4_gp  = str(r['p4_gp'])  # No crown on games played

        total_gp = str(r['total_gp'])  # No crown on total games played

        stats_text = (
            f"{mention}\n"
            f"**3 Player Stats**\n"
            f"Points: {p3_pts}\n"
            f"PPG: {p3_ppg}\n"
            f"Games Played: {p3_gp}\n"
            f"**4 Player Stats**\n"
            f"Points: {p4_pts}\n"
            f"PPG: {p4_ppg}\n"
            f"Games Played: {p4_gp}\n"
            f"**Total Games Played: {total_gp}**"
        )

        embed.add_field(name="\u200b", value=stats_text, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

''' Slash Command - Display Leaderboard '''
@bot.tree.command(name="leaderboard", description="Display the current leaderboard.", guild=MY_GUILD)
async def leaderboard(interaction: discord.Interaction):

    load_stats()

    public_url = dotenv_values(".env").get("NGROK_URL")
    


    # Send player stats after deferring
    await send_player_stats(interaction, stats, sort_by="total_gp")

    # Send the leaderboard URL as a follow-up
    if public_url is not "":
        await interaction.followup.send(
            f"🌐 You can also view the leaderboard here: {public_url}",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            "🌐 The web server is offline right now",
            ephemeral=True
        )
    

bot.run(TOKEN, log_handler = handler)
