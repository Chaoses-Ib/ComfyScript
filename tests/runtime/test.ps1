$ErrorActionPreference = 'Stop'
$outputTests = Join-Path $PSScriptRoot '../../../../output/tests'

$expectedFiles = @('virtual_00001_.png', 'real_00001_.png')
pushd $PSScriptRoot

Write-Host "=== Clearing output ===" -ForegroundColor Cyan
foreach ($file in $expectedFiles) {
    $path = Join-Path $outputTests $file
    if (Test-Path $path) {
        Remove-Item -Force $path
    }
}

Write-Host "=== Running virtual runtime ===" -ForegroundColor Cyan
python virtual.py @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "virtual.py failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "=== Running real runtime ===" -ForegroundColor Cyan
python real.py @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "real.py failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "=== Asserting output ===" -ForegroundColor Cyan
foreach ($file in 'virtual_00001_.png', 'real_00001_.png') {
    $path = Join-Path $outputTests $file
    if (!(Test-Path $path)) {
        Write-Host "Missing: $path" -ForegroundColor Red
        exit 1
    }
}

Write-Host "=== All tests passed ===" -ForegroundColor Green
popd

Write-Host "Manually test Jupyter Notebook"
