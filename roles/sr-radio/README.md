# sr-radio

Plays Sveriges Radio live streams (P4 Stockholm by default) through mpv,
controlled via CLI or a small HTTP API.

Two systemd user services for the `media` user:

- `sr-radio.service` — runs mpv against the current channel's stream.
  Started on demand; `play` enables it and `stop` disables it, so playback
  resumes after a power loss but stays off after a deliberate stop.
- `sr-radio-api.service` — stdlib Python HTTP API, enabled at boot.

Channels, API port and audio outputs are configured in `defaults/main.yml`
and rendered to `/opt/sr-radio/config.json`. The output is selectable
(GUI dropdown, `sr-radio output <id>`, or `POST /output`) between the
built-in 3.5mm jack (aux, default) and the USB sound card, so playback
does not follow the system default sink; list device names with
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
sr-radio output [id]      # show or set output (aux/usb)
sr-radio outputs
```

## Web GUI + HTTP API (port 8090)

`http://audiopi.local:8090/` serves a small GUI with channel selector,
output selector and play/stop button. `/mixer` (linked from the main
page) is a volume mixer with sliders for each output sink and each
currently playing stream (radio, Spotify, AirPlay, ...), backed by
`pactl`; WirePlumber remembers the volumes across reboots.

```
GET  /status              -> {"playing": bool, "channel": "p4stockholm", "output": "aux"}
GET  /channels            -> {"channels": [{"id": "p1", "name": "P1"}, ...], "default": "p4stockholm"}
GET  /outputs             -> {"outputs": [{"id": "aux", "name": "Aux"}, ...], "default": "aux"}
POST /play                body optional: {"channel": "p3"} (default: current channel)
POST /select              switch channel; applies immediately if playing
POST /output              body: {"output": "usb"}; applies immediately if playing
POST /stop
GET  /mixer.json          -> {"sinks": [{"id", "name", "volume"}], "streams": [...]}
POST /volume              body: {"type": "sink"|"stream", "id": ..., "volume": 0-100}
```

The GUI polls `/status` every 3 s and always mirrors the server state,
so multiple concurrently open GUIs stay in sync.

Example: `curl -X POST audiopi.local:8090/play`
