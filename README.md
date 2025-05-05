# Vernius
## Dune: Imperium Leaderboard Bot for Discord
Very simple Discord application to handle a very specific task for my Dune: Imperium board game group.
Rather than count wins arbitrarily, I spent a few hours of my Sunday making this bot to separate and allocate
points for 3-player and 4-player games. Also, it comes with a nifty leaderboard (and a web version) because Markdown
tables in Discord were not satisfactory for display.

## Setup
Setup is simple - just copy your authtokens for Discord and [ngrok](https://ngrok.com/).

- Install ngrok. Set up a free account. Copy your AUTHTOKEN from Settings.
- Create an application in Discord. Use the following permission integer: 1926762806384. Invite it to your server. Here is an example link: ```https://discord.com/oauth2/authorize?client_id=<id>>&permissions=1926762806384&integration_type=0&scope=bot+applications.commands```
- Copy the Guild (Server) ID of the server(s) you'd like to invite the bot to.
- Install the Python SDKs / dependencies in a virtual environment of your choice

Example initial .env:
```
DISCORD_TOKEN=<token>
GUILD_ID=<token>
NGROK_AUTHTOKEN=<token>
NGROK_URL=""
```