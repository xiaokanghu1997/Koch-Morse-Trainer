; Koch 安装脚本

#define MyAppName "Koch"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "xiaokanghu1997"
#define MyAppExeName "Koch.exe"
#define MyResourceGenExeName "Create Koch Morse Training Materials.exe"

[Setup]
AppId={{A3B2C1D4-E5F6-7890-ABCD-1234567890AB}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\Build
OutputBaseFilename=Koch_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardImageFile=logo.bmp
UninstallFilesDir={app}\Uninstall
UninstallDisplayName=Uninstall {#MyAppName}

; 要求管理员权限（因为要写入D盘）
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional options:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
; 主程序
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 资源生成器
Source: "..\dist\{#MyResourceGenExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 配置文件（如果有）
Source: "..\Config.py"; DestDir: "{app}"; Flags: ignoreversion
; Logo（如果有）
Source: "..\Logo\*"; DestDir: "D:\Program Files (x86)\Koch\Logo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单
Name: "{group}\Koch"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Create Koch Morse Training Materials"; Filename: "{app}\{#MyResourceGenExeName}"
Name: "{group}\Uninstall Koch"; Filename: "{uninstallexe}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; 快速启动
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; 安装后运行资源生成工具（可选）
Filename: "{app}\{#MyResourceGenExeName}"; Description: "Create Koch Morse Training Materials Now"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; 卸载时删除生成的文件
Type: filesandordirs; Name: "D:\Program Files (x86)\Koch"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not DirExists('D:\') then
  begin
    MsgBox('Drive D:\ not found, cannot install!', mbError, MB_OK);
    Result := False;
  end;
end;