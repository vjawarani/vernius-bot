from flask import Flask, render_template_string, request
from ngrok import ngrok
from dotenv import load_dotenv, set_key
import os
import json
import threading
import time
import requests

# --- Setup ---
load_dotenv()
ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN"))

app = Flask(__name__)
PORT = 5000

# --- Flask Route ---
@app.route('/', methods=['GET', 'POST'])
def leaderboard():
    try:
        with open('player_stats.json', 'r') as f:
            stats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "<h2>No leaderboard data available.</h2>"

    rows = []
    for player_id, modes in stats.items():
        p3 = modes.get("3", {})
        p4 = modes.get("4", {})
        p3_pts, p3_gp = p3.get("points", 0), p3.get("games_played", 0)
        p4_pts, p4_gp = p4.get("points", 0), p4.get("games_played", 0)
        p3_ppg = round(p3_pts / p3_gp, 2) if p3_gp else 0
        p4_ppg = round(p4_pts / p4_gp, 2) if p4_gp else 0
        total_gp = p3_gp + p4_gp

        rows.append(f"""
            <tr>
                <td>{player_id}</td>
                <td>{p3_pts}</td><td>{p3_gp}</td><td>{p3_ppg}</td>
                <td>{p4_pts}</td><td>{p4_gp}</td><td>{p4_ppg}</td>
                <td>{total_gp}</td>
            </tr>
        """)

    table = """
    <html>
        <head>
            <title>Leaderboard</title>
            <style>
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #999; padding: 8px; text-align: center; }}
                th {{ background-color: #eee; }}
            </style>
        </head>
        <body>
            <h2>Dune Leaderboard</h2>
            <table>
                <tr>
                    <th>Player ID</th><th>3P Points</th><th>3P Games</th><th>3P PPG</th>
                    <th>4P Points</th><th>4P Games</th><th>4P PPG</th><th>Total GP</th>
                </tr>
                {rows}
            </table>
        </body>
    </html>
    """.format(rows=''.join(rows))

    return render_template_string(table)

# --- Server Control ---
def start_flask():
    app.run(host='127.0.0.1', port=PORT, use_reloader=False)


def start_ngrok():
    tunnel = ngrok.forward(PORT)
    public_url = tunnel.url()
    print(f" * ngrok tunnel available at: {public_url}")
    set_key(".env", "NGROK_URL", public_url)
    return public_url

def start_server_and_tunnel():
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()
    time.sleep(3)
    start_ngrok()
    try:
        print("Server and tunnel running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

# --- Main Entry ---
if __name__ == "__main__":
    start_server_and_tunnel()
