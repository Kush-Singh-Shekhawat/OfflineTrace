$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONPATH = "$PWD\backend"
& ".\.venv\Scripts\python.exe" -m app.validator_node.main
