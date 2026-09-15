$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& .\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean TheoryDictationMaster.spec
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
$smoke = Start-Process -FilePath .\dist\TheoryDictationMaster.exe -ArgumentList '--self-test' -Wait -PassThru -WindowStyle Hidden
if ($smoke.ExitCode -ne 0) { throw 'Packaged smoke test failed' }
