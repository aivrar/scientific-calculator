# Build SuperCalc.exe as a single-file Windows binary.
# Run from the project directory:  .\build.ps1
$ErrorActionPreference = "Stop"

# Clean previous build
if (Test-Path .\build) { Remove-Item .\build -Recurse -Force }
if (Test-Path .\dist)  { Remove-Item .\dist  -Recurse -Force }
if (Test-Path .\SuperCalc.spec) { Remove-Item .\SuperCalc.spec -Force }

# Excluding heavy packages we don't use trims the exe by a lot.
$excludes = @(
    "PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "jupyter",
    "notebook", "tornado", "zmq", "pytest", "pandas", "sklearn",
    "tensorflow", "torch", "wx"
)
$excludeArgs = $excludes | ForEach-Object { "--exclude-module=$_" }

pyinstaller --noconfirm --onefile --windowed `
    --name SuperCalc `
    --collect-data tkinterdnd2 `
    --collect-data matplotlib `
    --hidden-import="matplotlib.backends.backend_tkagg" `
    --hidden-import="PIL._tkinter_finder" `
    @excludeArgs `
    super_calc.py

if ($LASTEXITCODE -ne 0) { throw "pyinstaller failed (exit $LASTEXITCODE)" }

$exe = Resolve-Path .\dist\SuperCalc.exe
$size = (Get-Item $exe).Length / 1MB
Write-Host ""
Write-Host "Built: $exe  ($([math]::Round($size,1)) MB)"
