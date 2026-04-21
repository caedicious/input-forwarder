; Input Forwarder — unified Inno Setup installer.
;
; Packages both the Sender (gaming PC) and Receiver (streaming PC) .exe
; files built by PyInstaller, and lets the user choose which role to
; install on this machine. Handles autostart, firewall rule, and
; scheduled-task registration automatically.
;
; Build via `build.bat` at the repo root, which produces
; `installer\Output\InputForwarderSetup.exe`.

#define MyAppName       "Input Forwarder"
#define MyAppVersion    "1.0.0"
#define MyAppPublisher  "CaedVT"
#define MyAppURL        "https://github.com/caedicious/input-forwarder"
#define SenderExe       "InputForwarderSender.exe"
#define ReceiverExe     "InputForwarderReceiver.exe"
#define ReceiverTask    "InputForwarderReceiver"
#define FirewallRule    "Input Forwarder Receiver"

[Setup]
AppId={{8E4B6F52-3D2A-4C6E-9F31-5B9A8D7E4A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=InputForwarderSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
CloseApplications=force
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\{#SenderExe}"; DestDir: "{app}"; Flags: ignoreversion; Check: IsSenderSelected
Source: "..\dist\{#ReceiverExe}"; DestDir: "{app}"; Flags: ignoreversion; Check: IsReceiverSelected

[Icons]
; Start Menu
Name: "{group}\{#MyAppName} Sender"; Filename: "{app}\{#SenderExe}"; Check: IsSenderSelected
Name: "{group}\{#MyAppName} Receiver"; Filename: "{app}\{#ReceiverExe}"; Check: IsReceiverSelected
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
; Sender autostart — per-user startup folder (no admin needed at runtime)
Name: "{userstartup}\{#MyAppName} Sender"; Filename: "{app}\{#SenderExe}"; Check: IsSenderSelected

[Run]
; Receiver needs an admin scheduled task so SendInput works in elevated games.
Filename: "schtasks.exe"; \
  Parameters: "/Create /TN ""{#ReceiverTask}"" /TR ""\""{app}\{#ReceiverExe}\""""  /SC ONLOGON /RL HIGHEST /F"; \
  Flags: runhidden; StatusMsg: "Registering receiver autostart (admin scheduled task)..."; \
  Check: IsReceiverSelected

; Receiver also needs an inbound firewall allow rule so the sender can reach it over UDP.
Filename: "netsh.exe"; \
  Parameters: "advfirewall firewall add rule name=""{#FirewallRule}"" dir=in action=allow program=""{app}\{#ReceiverExe}"" enable=yes profile=private,domain"; \
  Flags: runhidden; StatusMsg: "Adding Windows Firewall rule for receiver..."; \
  Check: IsReceiverSelected

; Launch the sender on finish so the first-run setup wizard appears.
Filename: "{app}\{#SenderExe}"; \
  Description: "Launch Sender and complete setup"; \
  Flags: nowait postinstall skipifsilent unchecked; Check: IsSenderSelected

; Launch the receiver on finish (inherits installer elevation) so its first-run wizard appears.
Filename: "{app}\{#ReceiverExe}"; \
  Description: "Launch Receiver and complete setup"; \
  Flags: nowait postinstall skipifsilent unchecked; Check: IsReceiverSelected

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""{#ReceiverTask}"" /F"; \
  Flags: runhidden; RunOnceId: "DelReceiverTask"
Filename: "netsh.exe"; Parameters: "advfirewall firewall delete rule name=""{#FirewallRule}"""; \
  Flags: runhidden; RunOnceId: "DelReceiverFW"
; Kill any running instances so we can delete files cleanly.
Filename: "taskkill.exe"; Parameters: "/F /IM {#SenderExe}"; Flags: runhidden; RunOnceId: "KillSender"
Filename: "taskkill.exe"; Parameters: "/F /IM {#ReceiverExe}"; Flags: runhidden; RunOnceId: "KillReceiver"

[UninstallDelete]
Type: files; Name: "{userstartup}\{#MyAppName} Sender.lnk"

[Code]
var
  RolePage: TInputOptionWizardPage;

procedure InitializeWizard;
begin
  RolePage := CreateInputOptionPage(wpWelcome,
    'Choose this PC''s role',
    'Which part of Input Forwarder should be installed on THIS computer?',
    'Select one option. You will run this installer on the other PC with the opposite role.' + #13#10 +
    'If you are just testing on a single machine, pick "Both".',
    True, False);
  RolePage.Add('Gaming PC (Sender) — captures your mouse/keyboard/controller input and sends it over the LAN');
  RolePage.Add('Streaming PC (Receiver) — receives input and replays it as real keypresses (runs as admin)');
  RolePage.Add('Both — install sender and receiver on this PC (single-machine testing only)');
  RolePage.SelectedValueIndex := 0;
end;

function IsSenderSelected: Boolean;
begin
  Result := (RolePage.SelectedValueIndex = 0) or (RolePage.SelectedValueIndex = 2);
end;

function IsReceiverSelected: Boolean;
begin
  Result := (RolePage.SelectedValueIndex = 1) or (RolePage.SelectedValueIndex = 2);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;
