from flask import Flask, jsonify, send_file, Response
from ngrok import ngrok
from dotenv import load_dotenv, set_key
import os
import json
import threading
import time
import queue

# --- Setup ---
load_dotenv()
ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN"))

app = Flask(__name__)
PORT = 5000

# --- SSE Setup ---
event_queue = queue.Queue()

def event_stream():
    """Yield messages to all connected clients when a refresh is triggered."""
    while True:
        msg = event_queue.get()  # Blocks until item is available
        yield f"data: {msg}\n\n"

@app.route('/events')
def sse():
    """SSE endpoint clients can listen to."""
    return Response(event_stream(), content_type='text/event-stream')

def trigger_refresh():
    """Push a refresh message to all clients."""
    print("Triggering refresh event to front-end clients...")
    event_queue.put("refresh")

# --- API Endpoint ---
@app.route("/api/leaderboard")
def api_leaderboard():
    try:
        with open('player_stats.json', 'r') as f:
            stats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify([])

    leaderboard_data = []
    for player_id, data in stats.items():
        nickname = data.get("nickname", player_id)
        avatar = data.get("avatar_url", "")
        p3 = data.get("3", {})
        p4 = data.get("4", {})

        p3_pts = p3.get("points", 0)
        p3_gp = p3.get("games_played", 0)
        p4_pts = p4.get("points", 0)
        p4_gp = p4.get("games_played", 0)
        p3_ppg = round(p3_pts / p3_gp, 2) if p3_gp else 0
        p4_ppg = round(p4_pts / p4_gp, 2) if p4_gp else 0
        total_gp = p3_gp + p4_gp

        leaderboard_data.append([
            player_id, nickname, avatar,
            str(p3_pts), str(p3_gp), f"{p3_ppg:.2f}",
            str(p4_pts), str(p4_gp), f"{p4_ppg:.2f}",
            str(total_gp)
        ])

    return jsonify(leaderboard_data)

# --- HTML UI ---
@app.route("/")
def serve_html():
    return send_file("templates/leaderboard.html")

# --- Server Control ---
def start_flask():
    app.run(host="127.0.0.1", port=PORT, use_reloader=False)

def start_ngrok():
    tunnel = ngrok.connect(PORT)
    public_url = tunnel.url()
    print(f" * ngrok tunnel available at: {public_url}")
    set_key(".env", "NGROK_URL", public_url)
    return public_url

def start_server_and_tunnel():
    threading.Thread(target=start_flask, daemon=True).start()
    time.sleep(2)
    url = start_ngrok()
    print("Server running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        set_key(".env", "NGROK_URL", "")
        print("Shutting down...")

# --- Main Entry ---
if __name__ == "__main__":
    start_server_and_tunnel()
