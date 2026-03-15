#!/usr/bin/python3
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Bluetooth auto-reconnect daemon for headless Raspberry Pi speaker.
# Tracks the last connected device and reconnects it with exponential backoff.

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from pathlib import Path

BUS_NAME = 'org.bluez'

BACKOFF_INITIAL = 5    # seconds before first reconnect attempt
BACKOFF_MAX = 300      # cap at 5 minutes
BACKOFF_FACTOR = 2

STATE_FILE = Path.home() / '.bt-last-device'

bus = None
mainloop = None
pending = {}  # path -> {'timer_id': int}


def save_last_device(path):
    STATE_FILE.write_text(path)


def load_last_device():
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip() or None
    return None


def is_paired(path):
    try:
        props = dbus.Interface(
            bus.get_object(BUS_NAME, path),
            'org.freedesktop.DBus.Properties'
        )
        return bool(props.Get('org.bluez.Device1', 'Paired'))
    except dbus.DBusException:
        return False


def is_connected(path):
    try:
        props = dbus.Interface(
            bus.get_object(BUS_NAME, path),
            'org.freedesktop.DBus.Properties'
        )
        return bool(props.Get('org.bluez.Device1', 'Connected'))
    except dbus.DBusException:
        return False


def get_device_name(path):
    try:
        props = dbus.Interface(
            bus.get_object(BUS_NAME, path),
            'org.freedesktop.DBus.Properties'
        )
        return str(props.Get('org.bluez.Device1', 'Name'))
    except dbus.DBusException:
        return path


def connect_device(path):
    try:
        dev = dbus.Interface(
            bus.get_object(BUS_NAME, path),
            'org.bluez.Device1'
        )
        dev.Connect()
        print(f"[bt-reconnect] Connected to {get_device_name(path)}")
        return True
    except dbus.DBusException as e:
        print(f"[bt-reconnect] Connect failed for {get_device_name(path)}: {e.get_dbus_message()}")
        return False


def cancel_pending(path):
    entry = pending.pop(path, None)
    if entry:
        GLib.source_remove(entry['timer_id'])


def schedule(path, delay):
    cancel_pending(path)

    print(f"[bt-reconnect] Reconnect attempt for {get_device_name(path)} in {delay}s")

    def attempt():
        if is_connected(path):
            print(f"[bt-reconnect] {get_device_name(path)} already connected, cancelling")
            pending.pop(path, None)
            return False

        if connect_device(path):
            pending.pop(path, None)
        else:
            next_delay = min(delay * BACKOFF_FACTOR, BACKOFF_MAX)
            schedule(path, next_delay)

        return False  # one-shot timer

    tid = GLib.timeout_add_seconds(delay, attempt)
    pending[path] = {'timer_id': tid}


def on_properties_changed(iface, changed, invalidated, path=None):
    if iface != 'org.bluez.Device1' or path is None:
        return
    if 'Connected' not in changed:
        return

    if changed['Connected']:
        cancel_pending(path)
        name = get_device_name(path)
        print(f"[bt-reconnect] {name} connected — saving as last device")
        save_last_device(path)
    else:
        last = load_last_device()
        if path != last:
            print(f"[bt-reconnect] {get_device_name(path)} disconnected (not last device, ignoring)")
            return
        print(f"[bt-reconnect] {get_device_name(path)} disconnected — scheduling reconnect")
        schedule(path, BACKOFF_INITIAL)


def reconnect_last_device():
    """On startup, reconnect the last known device if it's paired and disconnected."""
    path = load_last_device()
    if not path:
        print("[bt-reconnect] No last device recorded, nothing to reconnect")
        return False

    if not is_paired(path):
        print(f"[bt-reconnect] Last device {path} is no longer paired, skipping")
        return False

    if is_connected(path):
        print(f"[bt-reconnect] {get_device_name(path)} already connected")
        return False

    print(f"[bt-reconnect] Reconnecting last device: {get_device_name(path)}")
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

    # Give BlueZ a moment to settle before reconnecting
    GLib.timeout_add_seconds(10, reconnect_last_device)

    print("[bt-reconnect] Started")
    mainloop = GLib.MainLoop()
    mainloop.run()
