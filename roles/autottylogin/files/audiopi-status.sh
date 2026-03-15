#!/bin/bash
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

svc_status() {
    if pgrep -u media -f "$1" > /dev/null 2>&1; then
        echo -e "    ${GREEN}●${NC} $2"
    else
        echo -e "    ${RED}●${NC} $2"
    fi
}

pw_module_status() {
    if pw-cli info all 2>/dev/null | grep -q "$1"; then
        echo -e "    ${GREEN}●${NC} $2"
    else
        echo -e "    ${RED}●${NC} $2"
    fi
}

IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "  ${BOLD}audiopi.local${NC} (${IP})"
echo "  ────────────────────────────────────"
echo ""
echo "  Services:"
svc_status librespot      "Spotify Connect  (librespot)"
svc_status shairport-sync "AirPlay          (shairport-sync)"
svc_status gmediarender   "DLNA             (gmediarender)"
svc_status speaker-agent  "Bluetooth        (speaker-agent)"
svc_status bt-reconnect   "BT Reconnect     (bt-reconnect)"
pw_module_status roc-source "ROC Streaming    (pipewire module)"
svc_status wireplumber    "Session Manager  (wireplumber)"
echo ""
echo "  Commands:"
echo "    pulsemixer      volume control"
echo "    cava            audio visualizer"
echo "    sudo bt-pair    BT pairing (3 min)"
echo ""
echo "  Logs:"
echo "    journalctl --user -u speaker-agent -f"
echo "    journalctl --user -u bt-reconnect -f"
echo "    journalctl --user -u librespot -f"
echo "    journalctl --user -u shairport-sync -f"
echo "    journalctl --user -u dlna-renderer -f"
echo "    journalctl --user -u pipewire -f        (includes ROC)"
echo ""
