#!/usr/bin/env python3
"""Spotify Bridge API — serves now-playing data and dithered album art for Watchy."""

import os
import logging

from flask import Flask, jsonify, request, redirect, Response
from auth import get_spotify_client
from dither import fetch_and_dither, fetch_and_dither_raw

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

ART_SIZE = int(os.environ.get("SPOTIFY_BRIDGE_ART_SIZE", "150"))
CACHE_DIR = os.environ.get("SPOTIFY_BRIDGE_CACHE_DIR", "/tmp/spotify-bridge")

# ---------- Auth endpoints (one-time setup) ----------


@app.route("/login")
def login():
    """Redirect to Spotify authorization page."""
    _, auth_manager = get_spotify_client()
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Handle Spotify OAuth callback and cache the token."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "missing code parameter"}), 400

    _, auth_manager = get_spotify_client()
    auth_manager.get_access_token(code)
    return jsonify({"status": "authenticated", "message": "Token cached. You can close this page."})


# ---------- Now-playing endpoints ----------


@app.route("/now-playing")
def now_playing():
    """Return current playback state as JSON.

    Response:
        {
            "is_playing": true,
            "track": "Song Name",
            "artist": "Artist Name",
            "album": "Album Name",
            "progress_ms": 45000,
            "duration_ms": 210000,
            "album_art_url": "https://i.scdn.co/image/...",
            "track_uri": "spotify:track:..."
        }
    """
    try:
        sp, _ = get_spotify_client()
        playback = sp.current_playback()
    except Exception as e:
        log.error("Spotify API error: %s", e)
        return jsonify({"error": "not_authenticated", "detail": str(e)}), 401

    if not playback or not playback.get("item"):
        return jsonify({
            "is_playing": False,
            "track": "",
            "artist": "",
            "album": "",
            "progress_ms": 0,
            "duration_ms": 0,
            "album_art_url": "",
            "track_uri": "",
        })

    item = playback["item"]
    images = item.get("album", {}).get("images", [])
    # Pick smallest image >= our target size, fallback to first
    art_url = ""
    if images:
        suitable = [img for img in images if img.get("width", 0) >= ART_SIZE]
        art_url = (suitable[-1] if suitable else images[0])["url"]

    return jsonify({
        "is_playing": playback.get("is_playing", False),
        "track": item.get("name", ""),
        "artist": ", ".join(a["name"] for a in item.get("artists", [])),
        "album": item.get("album", {}).get("name", ""),
        "progress_ms": playback.get("progress_ms", 0),
        "duration_ms": item.get("duration_ms", 0),
        "album_art_url": art_url,
        "track_uri": item.get("uri", ""),
    })


@app.route("/album-art")
def album_art_bmp():
    """Return dithered 1-bit BMP of current album art.

    Query params:
        format: 'bmp' (default) or 'raw' (packed 1-bit pixels for GxEPD2)
    """
    try:
        sp, _ = get_spotify_client()
        playback = sp.current_playback()
    except Exception as e:
        return jsonify({"error": "not_authenticated", "detail": str(e)}), 401

    if not playback or not playback.get("item"):
        return Response(b"", status=204)

    images = playback["item"].get("album", {}).get("images", [])
    if not images:
        return Response(b"", status=204)

    suitable = [img for img in images if img.get("width", 0) >= ART_SIZE]
    art_url = (suitable[-1] if suitable else images[0])["url"]

    fmt = request.args.get("format", "bmp")

    if fmt == "raw":
        data = fetch_and_dither_raw(art_url, size=ART_SIZE, cache_dir=CACHE_DIR)
        return Response(data, mimetype="application/octet-stream")
    else:
        data = fetch_and_dither(art_url, size=ART_SIZE, cache_dir=CACHE_DIR)
        return Response(data, mimetype="image/bmp")


# ---------- Playback control endpoints ----------


@app.route("/play", methods=["POST"])
def play():
    """Resume playback."""
    try:
        sp, _ = get_spotify_client()
        sp.start_playback()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/pause", methods=["POST"])
def pause():
    """Pause playback."""
    try:
        sp, _ = get_spotify_client()
        sp.pause_playback()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/next", methods=["POST"])
def next_track():
    """Skip to next track."""
    try:
        sp, _ = get_spotify_client()
        sp.next_track()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/previous", methods=["POST"])
def previous_track():
    """Skip to previous track."""
    try:
        sp, _ = get_spotify_client()
        sp.previous_track()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("SPOTIFY_BRIDGE_PORT", "5000"))
    log.info("Starting Spotify Bridge on port %d", port)
    app.run(host="0.0.0.0", port=port)