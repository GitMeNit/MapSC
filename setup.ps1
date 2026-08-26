# MapSC environment setup (Windows)
# Uses Python 3.11 via the py launcher to avoid MSYS Python on PATH.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' not found. Install Python 3.11+ from python.org."
}

Write-Host "Creating virtualenv (.venv) with Python 3.11..."
py -3.11 -m venv .venv

Write-Host "Installing dependencies..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt

Write-Host "Running smoke test..."
.\.venv\Scripts\python.exe hello_world.py

Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1"
