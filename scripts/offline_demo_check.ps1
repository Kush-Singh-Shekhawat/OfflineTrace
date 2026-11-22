$ErrorActionPreference = "Stop"
Write-Host "Checking local prerequisites..."
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python launcher (py) not found." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js not found." }
if (-not (Test-Path ".env")) { Write-Warning ".env is missing; copy .env.example to .env." }
if (-not (Test-Path "frontend/node_modules")) { Write-Warning "Frontend dependencies missing; run npm --prefix frontend install." }
Write-Host "Prerequisite check complete. Start backend and frontend in separate terminals."
