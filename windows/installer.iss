[Setup]
AppId={{@@APP_ID@@}
AppName=@@APP_NAME@@
AppVersion=1.2.1
DefaultDirName={localappdata}\Programs\ExeCreator\@@APP_ID@@
DefaultGroupName=@@APP_NAME@@
UninstallDisplayName=@@APP_NAME@@
UninstallDisplayIcon={app}\@@APP_NAME@@.exe
OutputDir=@@OUTPUT@@
OutputBaseFilename=@@APP_NAME@@-Setup
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=no
SetupLogging=yes
SetupIconFile=@@PAYLOAD@@\app.ico

[Tasks]
Name: "desktopicon"; Description: "Ish stolida yuborilgan rasm bilan yorliq yaratish"

[Files]
Source: "@@PAYLOAD@@\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "@@BOOTSTRAPPER@@"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\@@APP_NAME@@"; Filename: "{app}\@@APP_NAME@@.exe"; IconFilename: "{app}\app.ico"
Name: "{autodesktop}\@@APP_NAME@@"; Filename: "{app}\@@APP_NAME@@.exe"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Run]
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Microsoft WebView2 tayyorlanmoqda (internet kerak bo'lishi mumkin)…"; Flags: waituntilterminated; Check: NeedsWebView2
Filename: "{app}\@@APP_NAME@@.exe"; Description: "Dasturni ochish"; Flags: nowait postinstall skipifsilent

[Code]
function NeedsWebView2: Boolean;
var Version: String;
begin
  Result := not ((RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0')) or
    (RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) and (Version <> '') and (Version <> '0.0.0.0')));
end;

function InitializeSetup: Boolean;
var Release: Cardinal;
begin
  Result := RegQueryDWordValue(HKLM32, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Release', Release) and (Release >= 528040);
  if not Result then
    MsgBox('Avval Microsoft .NET Framework 4.8 o''rnating: https://dotnet.microsoft.com/download/dotnet-framework/net48', mbError, MB_OK);
end;
