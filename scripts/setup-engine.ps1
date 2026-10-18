param([string]$PythonExecutable = $env:NIKKE_PYTHON)
$ErrorActionPreference = 'Stop'
if (-not $PythonExecutable) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $PythonExecutable = if (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { 'python' }
}
& $PythonExecutable (Join-Path $PSScriptRoot 'setup-engine.py')
if ($LASTEXITCODE -ne 0) { throw 'Engine setup failed' }
Write-Output 'Start with node server.mjs, or double-click Start-NikkeTools.cmd.'
