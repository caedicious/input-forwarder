# Building the Installer

This is the maintainer guide for producing `InputForwarderSetup.exe`, the
single installer that end users download and run. End-user install steps
live in [DEPLOYMENT.md](DEPLOYMENT.md).

## One-time setup

Install these on the build machine (Windows):

1. **Python 3.10+** — <https://www.python.org/downloads/>
   (check *Add Python to PATH* during install)
2. **Python dependencies**
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```
3. **Inno Setup 6** — <https://jrsoftware.org/isdl.php>
   (the default install path is auto-detected by `build.bat`)

## Build

From the repo root:

```
build.bat
```

This runs three steps:

1. Cleans `build\`, `dist\`, `installer\Output\`, and old `.spec` files.
2. Runs PyInstaller twice to produce:
   - `dist\InputForwarderSender.exe`
   - `dist\InputForwarderReceiver.exe`
3. Runs Inno Setup's `ISCC.exe` against `installer\InputForwarder.iss`
   to produce:
   - `installer\Output\InputForwarderSetup.exe`

Upload `InputForwarderSetup.exe` as the asset on a GitHub Release.

## What the installer does

On the target machine the installer:

- Shows a **role selection page** (Gaming PC / Streaming PC / Both).
- Copies the selected `.exe`(s) to `%ProgramFiles%\Input Forwarder\`.
- Creates Start Menu shortcuts.
- **Sender role:** adds a shortcut to the current user's Startup folder
  so it launches at login.
- **Receiver role:**
  - Registers the `InputForwarderReceiver` scheduled task to run at
    logon with `HIGHEST` (admin) privileges — required for `SendInput`
    to work in elevated windows.
  - Adds an inbound Windows Firewall allow rule for the receiver `.exe`
    on private/domain profiles.
- Optionally launches the app(s) on finish so the first-run config
  wizard appears (IP/port prompt).

Uninstall reverses all of the above: deletes the scheduled task,
firewall rule, shortcuts, and files.

## File layout

```
input-forwarder/
├── sender.pyw              # Sender source
├── receiver.pyw            # Receiver source
├── build.bat               # Build pipeline entry point
├── installer/
│   ├── InputForwarder.iss  # Inno Setup script (single installer)
│   └── Output/             # Built installer (gitignored)
├── dist/                   # PyInstaller output (gitignored)
└── build/                  # PyInstaller temp (gitignored)
```

## Version bumping

Edit `#define MyAppVersion` at the top of
`installer\InputForwarder.iss` before each release build.

## Icons (optional)

The `assets\` directory is currently empty. To brand the apps and
installer, drop a `.ico` file in `assets\` and add to:

- `build.bat` — add `--icon assets\icon.ico` to each PyInstaller call.
- `InputForwarder.iss` — add `SetupIconFile=..\assets\icon.ico` under
  `[Setup]`.

## Common issues

- **Antivirus flags the `.exe`** — PyInstaller one-file binaries are a
  known false-positive magnet. Sign the installer if distributing
  widely, or provide SHA256 hashes on the release page.
- **Tray icon missing in frozen sender** — make sure
  `--collect-submodules pystray` and `--collect-submodules PIL` are
  passed (they are in `build.bat`).
- **Receiver `SendInput` silently fails after install** — confirm the
  scheduled task exists: `schtasks /Query /TN InputForwarderReceiver`.
  If not, re-run the installer as admin.
