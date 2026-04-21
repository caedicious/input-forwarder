# Input Forwarder

Dual-PC input forwarding for Windows. Captures mouse, keyboard, and Xbox
controller input on one PC and simulates it as real input on another PC
over UDP.

Built for VTubing / dual-PC streaming setups — trigger VNyan blendshapes
from gameplay inputs, forward push-to-talk to Discord on the streaming
PC, etc.

## Components

- **`sender.pyw`** — runs on the gaming PC. Tray app with a GUI for
  configuring trigger → output mappings.
- **`receiver.pyw`** — runs on the streaming PC. Headless, runs as
  administrator (required for `SendInput` to work across all windows).

## Install (end users)

Download `InputForwarderSetup.exe` from the
[Releases page](https://github.com/caedicious/input-forwarder/releases)
and run it on **both** PCs, picking a different role on each:

- On the **gaming PC**: choose *Gaming PC (Sender)*.
- On the **streaming PC**: choose *Streaming PC (Receiver)*.

The installer handles firewall rules, autostart, and the admin
scheduled task automatically. The apps' first-run wizards then walk you
through IP/port configuration.

Full step-by-step guide: **[DEPLOYMENT.md](DEPLOYMENT.md)**.

## Run from source (developers)

```
pip install -r requirements.txt
pythonw sender.pyw       # on the gaming PC
pythonw receiver.pyw     # on the streaming PC (admin terminal)
```

First launch on each machine runs the setup wizard to configure IP
and port.

## Building the installer

See **[BUILDING.md](BUILDING.md)**. Short version:

```
pip install pyinstaller
build.bat
```

Requires Inno Setup 6 to be installed.

## Output Modes

| Mode | Behavior |
|------|----------|
| `single` | One tap on trigger press, nothing on release |
| `hold` | Key down on press, key up on release |
| `repeat` | Spam key while held |
| `repeat_paired` | Spam in pairs (on+off), always ends in "off" state |
| `toggle_repeat` | Activate on press, spam while held, deactivate on release |
| `press_both` | One tap on press, one tap on release |

## Known Limitations

- Mouse Without Borders forwards the receiver's simulated keypresses
  back to the sender. Disable MWB or configure exclusions while gaming.
- Auto-discovery (UDP broadcast) does not cross subnets or VPNs.
  Target the LAN IP, not a Tailscale / VPN address.
- Receiver must run elevated — `SendInput` is blocked by UIPI otherwise.
  The installer handles this via a `HIGHEST`-level scheduled task.

## License

MIT
