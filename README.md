# Input Forwarder

Dual-PC input forwarding for Windows. Captures mouse, keyboard, and Xbox controller inputs on PC1 and simulates them as real inputs on PC2 over UDP.

Built for VTubing / dual-PC streaming setups — trigger VNyan blendshapes from gameplay inputs, forward push-to-talk to Discord on the streaming PC.

## Components

- **`sender.pyw`** — PC1 (gaming PC). Tray app with GUI for configuring trigger → output mappings.
- **`receiver.pyw`** — PC2 (streaming PC). Headless. Must run as administrator.

## Install

```
pip install -r requirements.txt
```

## Run

**PC1 (sender):**
```
pythonw sender.pyw
```

**PC2 (receiver, admin terminal):**
```
pythonw receiver.pyw
```

First launch on each machine runs a setup wizard.

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

- Mouse Without Borders forwards PC2's simulated keypresses back to PC1. Disable MWB or configure exclusions during gaming.
- Auto-discovery (UDP broadcast) does not cross subnets or VPNs. Target the LAN IP, not Tailscale.
- Receiver must run elevated — SendInput is blocked by UIPI otherwise.

## License

MIT
