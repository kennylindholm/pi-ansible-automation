# sr-radio

Plays Sveriges Radio live streams (P4 Stockholm by default) through mpv,
controlled via CLI or a small HTTP API.

Two systemd user services for the `media` user:

- `sr-radio.service` — runs mpv against the current channel's stream.
  Started on demand; `play` enables it and `stop` disables it, so playback
  resumes after a power loss but stays off after a deliberate stop.
- `sr-radio-api.service` — stdlib Python HTTP API, enabled at boot.

Channels, API port and audio output device are configured in
`defaults/main.yml` and rendered to `/opt/sr-radio/config.json`.
Playback is pinned to the built-in 3.5mm jack (`sr_radio_audio_device`)
so it does not follow the default sink; list device names with
`mpv --audio-device=help`. Stream URLs use SR's stable channel-id
redirects, AAC 320 kbps variant (the plain `<id>.mp3` URLs are only
96 kbps MP3). List all channel ids:
`https://api.sr.se/api/v2/channels?liveaudiotemplateid=3&audioquality=hi`

## CLI

```
sr-radio play [channel]   # default: p4stockholm
sr-radio stop
sr-radio status
sr-radio channels
```

## Web GUI + HTTP API (port 8090)

`http://audiopi.local:8090/` serves a small GUI with channel selector
and play/stop button.

```
GET  /status              -> {"playing": bool, "channel": "p4stockholm"}
GET  /channels            -> {"channels": [{"id": "p1", "name": "P1"}, ...], "default": "p4stockholm"}
POST /play                body optional: {"channel": "p3"} (default: current channel)
POST /select              switch channel; applies immediately if playing
POST /stop
```

The GUI polls `/status` every 3 s and always mirrors the server state,
so multiple concurrently open GUIs stay in sync.

Example: `curl -X POST audiopi.local:8090/play`
