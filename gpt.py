import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv
from discord_slash import SlashCommand, SlashContext
import json

# Initialize bot and slash commands
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
slash = SlashCommand(bot, sync_commands=True)

# Data structure to store player stats
player_stats = {}

# Function to save stats to a file
def save_stats():
    with open('player_stats.json', 'w') as f:
        json.dump(player_stats, f)

# Function to load stats from a file
def load_stats():
    global player_stats
    try:
        with open('player_stats.json', 'r') as f:
            player_stats = json.load(f)
    except FileNotFoundError:
        player_stats = {}

# Command to add a game result (automatically detects 3 or 4 players)
@slash.slash(name="addgame", description="Add a game result (3 or 4 players).")
async def add_game(ctx: SlashContext, *players: discord.Member):
    num_players = len(players)

    if num_players not in [3, 4]:
        await ctx.send("Please provide either 3 or 4 players.")
        return

    # Points distribution based on the number of players
    if num_players == 3:
        points_distribution = [2, 1, 0]
    elif num_players == 4:
        points_distribution = [3, 2, 1, 0]

    # Update player stats
    for idx, player in enumerate(players):
        if player.id not in player_stats:
            player_stats[player.id] = {'points': 0, 'games_played': 0}

        # Assign points based on position
        player_stats[player.id]['points'] += points_distribution[idx]
        player_stats[player.id]['games_played'] += 1

    # Save stats
    save_stats()

    # Prepare the result message
    result_message = ", ".join([f"{players[idx].name} - {points_distribution[idx]} points" for idx in range(num_players)])
    await ctx.send(f"Game added: {result_message}")

# Command to edit a player's score manually
@slash.slash(name="edit", description="Edit a player's score manually.")
async def edit_score(ctx: SlashContext, player: discord.Member, points: int):
    if player.id not in player_stats:
        player_stats[player.id] = {'points': 0, 'games_played': 0}

    player_stats[player.id]['points'] = points
    save_stats()
    await ctx.send(f"{player.name}'s score has been updated to {points} points.")

# Command to display a player's stats
@slash.slash(name="stats", description="Show the stats of a player.")
async def player_stats_cmd(ctx: SlashContext, player: discord.Member):
    if player.id not in player_stats:
        await ctx.send(f"{player.name} has not played any games yet.")
    else:
        points = player_stats[player.id]['points']
        games_played = player_stats[player.id]['games_played']
        if games_played > 0:
            ppg = points / games_played
        else:
            ppg = 0
        await ctx.send(f"{player.name}'s stats: {points} points, {games_played} games played, {ppg:.2f} points per game.")

# Command to list the leaderboard
@slash.slash(name="leaderboard", description="Show the leaderboard of all players.")
async def leaderboard(ctx: SlashContext):
    if not player_stats:
        await ctx.send("No player stats available.")
        return
    leaderboard_message = "Leaderboard:\n"
    sorted_stats = sorted(player_stats.items(), key=lambda x: x[1]['points'], reverse=True)
    for player_id, stats in sorted_stats:
        user = await bot.fetch_user(player_id)
        ppg = stats['points'] / stats['games_played'] if stats['games_played'] > 0 else 0
        leaderboard_message += f"{user.name}: {stats['points']} points, {stats['games_played']} games, {ppg:.2f} PPG\n"
    await ctx.send(leaderboard_message)

# Load stats when the bot starts
@bot.event
async def on_ready():
    load_stats()
    print(f'Bot logged in as {bot.user}')


load_dotenv()
token = os.getenv("DISCORD_TOKEN")
bot.run(token)