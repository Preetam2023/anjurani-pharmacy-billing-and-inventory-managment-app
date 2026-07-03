#define MyAppName "Anjurani Pharmacy"
#define MyAppVersion "1.1.0"
#define MyAppExeName "Anjurani Pharmacy.exe"

[Setup]
AppId={{A1B8D3D6-65E8-4B9E-8F25-4C5F1C5D7A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}

AppPublisher=Preetam Manna
AppPublisherURL=https://github.com/Preetam2023
AppSupportURL=https://github.com/Preetam2023/anjurani-pharmacy-billing-and-inventory-managment-app
AppUpdatesURL=https://github.com/Preetam2023/anjurani-pharmacy-billing-and-inventory-managment-app

AppVerName={#MyAppName} v{#MyAppVersion}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=Output
OutputBaseFilename=Anjurani_Pharmacy_Setup_v1.1.0

Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardImageStretch=no

SetupIconFile=assets\images\logo.ico
WizardImageFile=assets\installer\wizard.bmp
WizardSmallImageFile=assets\installer\wizard_small.bmp

PrivilegesRequired=lowest

CloseApplications=yes
RestartApplications=no

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

DisableProgramGroupPage=yes
DisableDirPage=no
DisableWelcomePage=no

UninstallDisplayIcon={app}\{#MyAppExeName}

VersionInfoVersion=1.1.0.0
VersionInfoCompany=Preetam Manna
VersionInfoDescription=Anjurani Pharmacy Desktop Software
VersionInfoCopyright=© 2026 Preetam Manna

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Shortcut"; GroupDescription: "Additional Icons:"; Flags: checkedonce

[Files]

Source: "dist\Anjurani Pharmacy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]

Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Anjurani Pharmacy"; Flags: nowait postinstall skipifsilent

[UninstallDelete]

Type: filesandordirs; Name: "{app}"