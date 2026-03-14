# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Ansible automation for Raspberry Pi devices running Raspberry Pi OS (Trixie, Debian arm64). Contains 22 reusable roles covering audio streaming, networking, system administration, PXE boot, and media services.

## Lint & Validation Commands

```bash
# YAML linting
yamllint .

# Ansible linting
ansible-lint roles/
```

## Running Playbooks

`ansible.cfg` sets the default inventory (`inventories/hosts.yml`) and roles path (`roles/`).

```bash
ansible-playbook playbooks/audiopi.yml          # Full audio stack (librespot + shairport + dlna + bluetooth)
```

## Architecture

### Audio Stack

All audio roles target the `audio` host group and use PipeWire (not PulseAudio). Audio services run as **per-user systemd services** (not system-wide), which requires the `autottylogin` role to enable auto-login for headless operation. This is a key dependency — audio services won't start on boot without it.

### Role Organization

Roles are self-contained under `roles/`. Each role typically includes `defaults/`, `vars/`, `handlers/`, `templates/`, and `files/`. Pre-compiled binaries (e.g., librespot ARM binaries) are stored in `files/`.

**Audio/streaming**: `librespot`, `shairport-sync`, `dlna-renderer`, `bluetooth-speaker`, `roc-streaming`, `spotify-watchy-bridge`

**System**: `autottylogin`, `ssh-hardening`, `avahi-discoverable`, `set-hostname`, `headless-powersave`, `disable-pi-radio`, `unattended-upgrades`

**Network**: `single-nic-firewall` (nftables NAT + DHCP + VLANs), `dnsmasq-tftp`, `dns-over-tls` (cloudflared), `duckdns`

**Boot/media**: `tftpd-server`, `nfs-boot-pi`, `kodi`, `steamlink-pi`, `pihole`

### Inventory & Variables

- Inventory: `inventories/hosts.yml` — currently defines the `audio` host group with `audiopi.local`
- Group vars: `inventories/group_vars/all/main.yml` — APT scheduling intervals
- Role-specific variables go in each role's `defaults/main.yml`

### YAML Style

`.yamllint` enforces max 220 characters per line (warning level) and requires document-start markers (`---`).

## Notable Required Variables

Some roles require variables to be set (no defaults):
- `kodi_remote_password` — Kodi web interface password
- `automatic_reboot_time` — Unattended upgrades reboot time (e.g., `"04:00"`)
- `cloudflared_release_ver` — Version of cloudflared to install

## CI

GitHub Actions (`.github/workflows/main.yml`) runs `yamllint .` and `ansible-lint roles/` on pull requests.
