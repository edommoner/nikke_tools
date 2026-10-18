param([string]$PythonExecutable = $env:NIKKE_PYTHON)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$revision = '23164e4a88fe46af609cc99b0de38a98313a5f4d'
if (-not $PythonExecutable) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $PythonExecutable = if (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { 'python' }
}
$upstreamRoot = Join-Path $taskRoot 'research\upstream'
$engineRoot = Join-Path $upstreamRoot 'nikke-calc-master'
if (-not (Test-Path -LiteralPath (Join-Path $engineRoot 'runner\sim.py'))) {
    New-Item -ItemType Directory -Path $upstreamRoot -Force | Out-Null
    $archive = Join-Path $upstreamRoot 'engine.zip'
    Invoke-WebRequest -Uri "https://codeload.github.com/Jgaram/nikke-calc/zip/$revision" -OutFile $archive
    $archiveRevision = & $PythonExecutable -c 'import sys,zipfile; print(zipfile.ZipFile(sys.argv[1]).comment.decode())' $archive
    if ($LASTEXITCODE -ne 0 -or $archiveRevision.Trim() -ne $revision) { throw 'Engine revision verification failed' }
    Expand-Archive -LiteralPath $archive -DestinationPath $upstreamRoot -Force
    $sourceRoot = [IO.Path]::GetFullPath((Join-Path $upstreamRoot "nikke-calc-$revision"))
    $expectedParent = [IO.Path]::GetFullPath($upstreamRoot) + [IO.Path]::DirectorySeparatorChar
    if (-not $sourceRoot.StartsWith($expectedParent, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected engine extraction path' }
    Rename-Item -LiteralPath $sourceRoot -NewName 'nikke-calc-master'
}
Write-Output "Engine ready: $engineRoot"
Write-Output 'Start with node server.mjs, or double-click Start-NikkeTools.cmd.'
