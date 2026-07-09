# PyInstaller-Build fuer den Werkstudent Job Agent
# Nutzung:  .\build.ps1   (aus dem Projektordner)
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed `
    --name "WerkstudentJobAgent" `
    --collect-all customtkinter `
    --add-data "config.json;." `
    run.py

Write-Host ""
Write-Host "Fertig. EXE liegt in dist\WerkstudentJobAgent.exe"
Write-Host "Wichtig: config.json und .env neben die EXE legen."
