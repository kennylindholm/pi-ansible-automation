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
svc_status wireplumber    "Session Manager  (wireplumber)"
echo ""
echo "  Commands:"
echo "    pulsemixer      volume control"
echo "    sudo bt-pair    BT pairing (3 min)"
echo ""
