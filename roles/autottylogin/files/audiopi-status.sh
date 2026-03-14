#!/bin/bash
# audiopi login status

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

svc_status() {
    if systemctl --user -M media@ is-active --quiet "$1" 2>/dev/null; then
        echo -e "  ${GREEN}●${NC} $2"
    else
        echo -e "  ${RED}●${NC} $2"
    fi
}

IP=$(hostname -I | awk '{print $1}')

echo ""
echo "  ┌─ audiopi.local ($IP) ──────────────────┐"
echo "  │                                            │"
echo "  │  Services                                  │"
svc_status librespot      "Spotify Connect     (librespot)      "
svc_status shairport-sync "AirPlay             (shairport-sync) "
svc_status gmediarender   "DLNA                (gmediarender)   "
svc_status speaker-agent  "Bluetooth           (speaker-agent)  "
svc_status wireplumber    "Session Manager     (wireplumber)    "
echo "  │                                            │"
echo "  │  Commands                                  │"
echo "  │    pulsemixer       volume control          │"
echo "  │    sudo bt-pair     BT pairing (3 min)      │"
echo "  │                                            │"
echo "  └────────────────────────────────────────────┘"
echo ""
