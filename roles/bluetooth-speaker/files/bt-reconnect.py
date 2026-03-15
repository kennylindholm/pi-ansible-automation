#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Bluetooth auto-reconnect daemon for headless Raspberry Pi speaker.
# Tracks the last connected device and reconnects it with exponential backoff.

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from pathlib import Path
from datetime import datetime

BUS_NAME = 'org.bluez'

BACKOFF_INITIAL = 5    # seconds before first reconnect attempt
BACKOFF_MAX = 300      # cap at 5 minutes
BACKOFF_FACTOR = 2

STATE_FILE = Path.home() / '.bt-last-device'

bus = None
mainloop = None
pending = {}  # path -> {'timer_id': int}


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] [bt-reconnect] {msg}", flush=True)


def save_last_device(path):
    STATE_FILE.write_text(path)
    log(f"Saved last device: {path}")


def load_last_device():
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip() or None
    return None


def get_device_props(path):
    props = dbus.Interface(
        bus.get_object(BUS_NAME, path, introspect=False),
        'org.freedesktop.DBus.Properties'
    )
    return props.GetAll('org.bluez.Device1')


def get_device_name(path):
    try:
        return str(get_device_props(path).get('Name', path))
    except dbus.DBusException:
        return path


def is_connected(path):
    try:
        return bool(get_device_props(path).get('Connected', False))
    except dbus.DBusException:
        return False


def connect_device(path):
    name = get_device_name(path)
    log(f"Attempting Connect() on {name} ({path})")
    try:
        dev = dbus.Interface(
            bus.get_object(BUS_NAME, path, introspect=False),
            'org.bluez.Device1'
        )
        dev.Connect()
        log(f"Connect() succeeded for {name}")
        return True
    except dbus.DBusException as e:
        log(f"Connect() failed for {name}: {e.get_dbus_name()} — {e.get_dbus_message()}")
        return False


def cancel_pending(path):
    entry = pending.pop(path, None)
    if entry:
        GLib.source_remove(entry['timer_id'])
        log(f"Cancelled pending reconnect for {get_device_name(path)}")


def schedule(path, delay):
    cancel_pending(path)

    name = get_device_name(path)
    log(f"Scheduling reconnect for {name} in {delay}s (backoff cap: {BACKOFF_MAX}s)")

    def attempt():
        log(f"Reconnect attempt for {name}")

        if is_connected(path):
            log(f"{name} is already connected, cancelling")
            pending.pop(path, None)
            return False

        if connect_device(path):
            pending.pop(path, None)
        else:
            next_delay = min(delay * BACKOFF_FACTOR, BACKOFF_MAX)
            log(f"Will retry in {next_delay}s")
            schedule(path, next_delay)

        return False  # one-shot timer

    tid = GLib.timeout_add_seconds(delay, attempt)
    pending[path] = {'timer_id': tid}


def on_properties_changed(iface, changed, invalidated, path=None):
    if iface != 'org.bluez.Device1' or path is None:
        return
    if 'Connected' not in changed:
        return

    name = get_device_name(path)
    if changed['Connected']:
        log(f"{name} connected")
        cancel_pending(path)
        save_last_device(path)
    else:
        last = load_last_device()
        log(f"{name} disconnected (last device: {last})")
        if path != last:
            log(f"Not the last device, ignoring")
            return
        log(f"Scheduling reconnect for last device {name}")
        schedule(path, BACKOFF_INITIAL)


def reconnect_last_device():
    """On startup, reconnect the last known device if it's paired and disconnected."""
    path = load_last_device()
    if not path:
        log("No last device recorded in state file, nothing to reconnect")
        return False

    log(f"Checking state of last device: {path}")

    try:
        props = get_device_props(path)
        paired = bool(props.get('Paired', False))
        connected = bool(props.get('Connected', False))
        name = str(props.get('Name', path))
        log(f"Device: {name} — paired={paired}, connected={connected}")
    except dbus.DBusException as e:
        log(f"BlueZ not ready ({e.get_dbus_name()}: {e.get_dbus_message()}), retrying in 15s")
        GLib.timeout_add_seconds(15, reconnect_last_device)
        return False

    if not paired:
        log(f"Device is no longer paired, clearing state file")
        STATE_FILE.unlink(missing_ok=True)
        return False

    if connected:
        log(f"{name} is already connected")
        return False

    log(f"Device {name} is paired but not connected — starting reconnect")
    schedule(path, BACKOFF_INITIAL)
    return False  # one-shot


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    bus.add_signal_receiver(
        on_properties_changed,
        signal_name='PropertiesChanged',
        dbus_interface='org.freedesktop.DBus.Properties',
        bus_name=BUS_NAME,
        arg0='org.bluez.Device1',
        path_keyword='path',
    )

    log(f"Started — will check for last device in 20s (state file: {STATE_FILE})")
    GLib.timeout_add_seconds(20, reconnect_last_device)

    mainloop = GLib.MainLoop()
    mainloop.run()
