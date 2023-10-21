if (Test-Path "venv") {
    Write-Host "Activating virtual environment..."
    & "venv\Scripts\Activate"
} else {
    Write-Host "Creating virtual environment..."

    python -m venv "venv"
    & "venv\Scripts\Activate"
}

$installedPackages = pip freeze
$requiredPackages = Get-Content "requirements.txt"
$missingPackages = $requiredPackages | Where-Object { $_ -notin $installedPackages }

if ($missingPackages.Count -eq 0) {
    Write-Host "All required packages are already installed."
} else {
    Write-Host "Installing missing packages from requirements.txt..."
    $missingPackages | ForEach-Object {
        pip install $_
    }
}

$runInBackground = Read-Host "Run in background? (y/n)"

if ($runInBackground -eq 'y') {
    pythonw.exe main.py
}
elseif ($runInBackground -eq 'n') {
    python main.py
}
