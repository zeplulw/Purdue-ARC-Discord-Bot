if (Test-Path "venv") {
    if (Test-Path env:VIRTUAL_ENV) {
        Write-Host -BackgroundColor Red -ForegroundColor Black "[VENV]" -NoNewLine
        Write-Host " Virtual environment already activated."
    }
    else {
        Write-Host -BackgroundColor Red -ForegroundColor Black "[VENV]" -NoNewLine
        Write-Host " Activating virtual environment..."
        & "venv\Scripts\Activate"
    }
} else {
    Write-Host -BackgroundColor Red -ForegroundColor Black "[VENV]" -NoNewLine
    Write-Host " Creating virtual environment..."

    python -m venv "venv"
    & "venv\Scripts\Activate"
}

$installedPackages = pip freeze
$requiredPackages = Get-Content "requirements.txt"
$missingPackages = $requiredPackages | Where-Object { $_ -notin $installedPackages }

if ($missingPackages.Count -eq 0) {
    Write-Host -BackgroundColor Blue -ForegroundColor Black "[PACKAGE]" -NoNewLine
    Write-Host " All required packages are already installed."
} else {
    Write-Host -BackgroundColor Blue -ForegroundColor Black "[PACKAGE]" -NoNewLine
    Write-Host " Installing missing packages from requirements.txt..."
    $missingPackages | ForEach-Object {
        pip install $_
        Write-Host -BackgroundColor Blue -ForegroundColor Black "[PACKAGE]" -NoNewLine
        Write-Host " Installed $_"
    }
}

$runInBackground = Read-Host "Run in background? (y/n)"
$runInBackground = $runInBackground.ToLower()

if ($runInBackground -eq 'y') {
    pythonw.exe main.py

    $process = Get-Process -Name "pythonw" | Sort-Object -Property StartTime -Descending | Select-Object -First 1
    Write-Host -BackgroundColor Red -ForegroundColor Black "-=-=-=- Background -=-=-=-"
    Write-Host "Process ID: $($process.Id).`n"
    Write-Host -BackgroundColor Red "To kill process:"
    Write-Host "Stop-Process -Id $($process.Id)"
}
elseif ($runInBackground -eq 'n') {
    Write-Host -BackgroundColor Red -ForegroundColor Black "-=-=-=- Foreground -=-=-=-"

    python main.py
}
