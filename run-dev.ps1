# Starts VERITAS locally: backend on :8000, frontend on :3000. Run from the veritas folder in PowerShell.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path "$root\backend\.venv")) {
  Write-Host "Creating Python venv + installing backend deps..."
  python -m venv "$root\backend\.venv"
  & "$root\backend\.venv\Scripts\pip.exe" install -r "$root\backend\requirements.txt" Pillow
}
if (-not (Test-Path "$root\backend\.env")) { Copy-Item "$root\backend\.env.example" "$root\backend\.env" }
if (-not (Test-Path "$root\frontend\node_modules")) {
  Write-Host "Installing frontend deps..."
  Push-Location "$root\frontend"; npm install; Pop-Location
}

Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\frontend'; npm run dev"
Write-Host "Backend: http://127.0.0.1:8000/api/docs   Frontend: http://localhost:3000"
