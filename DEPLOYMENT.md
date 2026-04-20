# Deployment

Install and autostart recipe for a dual-PC setup. The **sender** runs on
the gaming PC and the **receiver** runs on the streaming / secondary PC.
Both PCs must be on the same LAN.

## 1. Install Python

Install Python 3.10+ on both PCs from <https://www.python.org/downloads/>.
During install, check **Add Python to PATH**.

## 2. Sender PC

```
copy sender.pyw %USERPROFILE%\sender.pyw
pip install -r requirements.txt
```

Run once to complete the first-time setup wizard (which asks for the
receiver's LAN IP and port):

```
pythonw %USERPROFILE%\sender.pyw
```

### Autostart (optional)

Create a `.bat` file at
`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\InputForwarderSender.bat`:

```bat
@echo off
start "" pythonw "%USERPROFILE%\sender.pyw"
```

## 3. Receiver PC

The receiver must run **as administrator** for `SendInput` to work across
foreground windows. It has no pip dependencies — stdlib and ctypes only.

```
copy receiver.pyw %USERPROFILE%\receiver.pyw
```

Run once from an **elevated** terminal to complete the setup wizard
(which asks for the listen port — must match the sender):

```
pythonw %USERPROFILE%\receiver.pyw
```

### Autostart (scheduled task, admin PowerShell)

Replace `<PYTHONW_PATH>` with the absolute path to your `pythonw.exe`.
You can find it with `where.exe pythonw` in a normal terminal.

```powershell
$pythonw = '<PYTHONW_PATH>'   # e.g. 'C:\Users\<you>\AppData\Local\Programs\Python\Python312\pythonw.exe'
$action = New-ScheduledTaskAction -Execute $pythonw -Argument "$env:USERPROFILE\receiver.pyw"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest
Register-ScheduledTask -TaskName 'InputForwarderReceiver' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
```

## 4. Firewall

Windows Firewall will prompt on first run of the receiver — allow it on
**Private** networks so the sender can reach it over the LAN.

## Resetting config

Delete the corresponding config file to re-run the setup wizard:

- Sender: `%USERPROFILE%\input_forwarder_config.json`
- Receiver: `%USERPROFILE%\input_forwarder_receiver.json`

## Kill commands

Sender PC (Git Bash):
```bash
taskkill //F //IM pythonw.exe
```

Receiver PC (admin PowerShell):
```powershell
taskkill /F /IM pythonw.exe
```
