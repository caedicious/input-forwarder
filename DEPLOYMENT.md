# Installing Input Forwarder

This guide walks you through installing Input Forwarder on two Windows
PCs on the same LAN:

- **Gaming PC (Sender)** — the PC you play on; captures your input.
- **Streaming PC (Receiver)** — the PC your stream runs on; replays
  the input as real keypresses (e.g. to trigger VNyan blendshapes or
  Discord push-to-talk).

You will run the **same installer** on both PCs and pick a different
role on each one.

## 1. Download

Grab the latest `InputForwarderSetup.exe` from the
[Releases page](https://github.com/caedicious/input-forwarder/releases).

Copy it to both PCs.

## 2. Install on the Streaming PC (receiver) first

Doing this side first makes step 3 easier because you will need this
PC's LAN IP address.

1. **Right-click** `InputForwarderSetup.exe` → **Run as administrator**.
2. Click through the Welcome page.
3. On the role page, choose **"Streaming PC (Receiver)"**.
4. Accept the default install location and click **Install**.
5. Windows may prompt for firewall / UAC approval — allow it.
6. On the finish page, leave **"Launch Receiver and complete setup"**
   checked and click **Finish**.
7. The Receiver's first-run wizard appears — pick a UDP port
   (default `7777` is fine) and click **Save**.

Find the Streaming PC's LAN IP so you can enter it on the Gaming PC:

- Press `Win + R`, type `cmd`, press Enter.
- Run `ipconfig` and note the **IPv4 Address** on your active network
  adapter (usually starts with `192.168.` or `10.`). Do **not** use a
  VPN or virtual adapter address.

## 3. Install on the Gaming PC (sender)

1. **Right-click** `InputForwarderSetup.exe` → **Run as administrator**.
2. On the role page, choose **"Gaming PC (Sender)"**.
3. Click **Install**, then **Finish** with
   **"Launch Sender and complete setup"** checked.
4. The Sender's first-run wizard appears:
   - **Target IP:** the Streaming PC's IPv4 address from step 2.
   - **Target Port:** the same port you chose on the receiver (default
     `7777`).
5. Click **Save**. The main window opens. It will now auto-start with
   Windows from this point on.

## 4. Add your mappings

In the Sender window:

1. Click **Add Mapping**.
2. Click **Record** next to *Trigger Input* and press the key, mouse
   button, or controller button you want to use.
3. Click **Record** next to *Output Key* and press the key you want
   the Streaming PC to receive.
4. Pick an output **Mode** (see the README for what each one does).
5. Click **Save**.

Press **F9** to toggle the sender between armed and disarmed.
The tray icon turns red when disarmed.

## Resetting

Delete the config file to re-run a first-run wizard:

- Sender: `%USERPROFILE%\input_forwarder_config.json`
- Receiver: `%USERPROFILE%\input_forwarder_receiver.json`

## Uninstall

Use **Settings → Apps** (or Control Panel → Programs) and uninstall
**Input Forwarder**. This removes the app, the firewall rule, the
scheduled task, and the autostart shortcut. Your config files in
`%USERPROFILE%` are left in place — delete them manually if you want a
full clean.

## Troubleshooting

- **Sender says "sent" but nothing happens on the Streaming PC.**
  The receiver probably isn't running as admin. Re-run the installer
  as admin on the Streaming PC, or verify the scheduled task:
  open an admin PowerShell and run
  `schtasks /Query /TN InputForwarderReceiver`.
- **`OSError 10048` in the receiver.** An old instance is still
  holding the UDP port. Open an admin terminal and run
  `taskkill /F /IM InputForwarderReceiver.exe`.
- **Mouse Without Borders forwards keys both ways.** MWB will echo the
  Streaming PC's simulated keypresses back to the Gaming PC. Disable
  MWB or configure keyboard-sharing exclusions while gaming.
- **Auto-discovery doesn't work over Tailscale / VPN.** The sender
  must target the LAN IP, not a VPN-assigned one.
