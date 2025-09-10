# Lokaler Windows-Build (PowerShell)
# Nutzung: .\build.ps1

$ErrorActionPreference = "Stop"

# 1) Virtuelle Umgebung (optional, aber empfohlen)
if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

# 2) Aktivieren & Pip aktualisieren
. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip wheel

# 3) Abhängigkeiten installieren
python -m pip install -r requirements.txt

# 4) EXE bauen
$Entry = "src/InventarQRTool.py"
$Name  = "InventarQRTool"
$Icon  = "assets/app.ico"   # Entferne --icon, falls nicht vorhanden

py -3.12 -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name $Name `
    --icon $Icon `
    --add-data "assets;assets" `
    $Entry

Write-Host "`nBuild abgeschlossen. Datei unter dist/$Name.exe"
