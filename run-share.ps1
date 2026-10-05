# Starts backend + production frontend + ngrok tunnel, each in its own window.
# Leave those windows alone (pressing Ctrl+C in one stops it). Close them to stop sharing.
# Prereqs: backend venv installed, `npm install` done, `ngrok config add-authtoken ...` done once.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

Push-Location "$root\frontend"
if (-not (Test-Path ".next\BUILD_ID")) { Write-Host "Building frontend (first time only)..."; npm run build }
Pop-Location
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\frontend'; npm run start"

Start-Sleep -Seconds 6
Start-Process powershell -ArgumentList "-NoExit","-Command","ngrok http 3000"
Write-Host "Copy the https://....ngrok-free.app link shown in the ngrok window and send it to your friend."
Write-Host "Local check: http://localhost:3000   Backend health: http://127.0.0.1:8000/api/health"
