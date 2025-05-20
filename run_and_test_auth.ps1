# run_and_test_auth.ps1
# PowerShell script to run the backend and test authentication

# Set console encoding to handle special characters in output
[console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Colors for console output
$SUCCESS = "Green"
$ERROR = "Red"
$INFO = "Cyan"
$WARNING = "Yellow"

# Function to display formatted messages
function Write-Message {
    param (
        [string]$Message,
        [string]$Type = "INFO"
    )
    
    $color = $INFO
    switch ($Type) {
        "SUCCESS" { $color = $SUCCESS; $Message = "✓ $Message" }
        "ERROR" { $color = $ERROR; $Message = "✗ $Message" }
        "WARNING" { $color = $WARNING; $Message = "! $Message" }
        default { $Message = "i $Message" }
    }
    
    Write-Host $Message -ForegroundColor $color
}

# Display header
Write-Host "`n==== QUIZ APP AUTH TESTER ====`n" -ForegroundColor $INFO

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Message "Python detected: $pythonVersion" "SUCCESS"
} catch {
    Write-Message "Python not found in PATH. Please install Python and try again." "ERROR"
    exit 1
}

# Check if backend directory exists
$backendDir = ".\backend_v2"
if (-not (Test-Path $backendDir)) {
    Write-Message "Backend directory not found at $backendDir" "ERROR"
    exit 1
}

# Check if the Flask app is already running
$flaskRunning = $false
try {
    $testConnection = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET -ErrorAction Stop
    if ($testConnection.status -eq "ok") {
        Write-Message "Flask server is already running" "SUCCESS"
        $flaskRunning = $true
    }
} catch {
    Write-Message "Flask server is not running, will start it now" "INFO"
}

# Start Flask server if not running
$flaskJob = $null
if (-not $flaskRunning) {
    Write-Message "Starting Flask server from $backendDir..." "INFO"
    
    # Change to the backend directory
    Set-Location $backendDir
    
    # Check for virtual environment
    $venvDir = "..\venv"
    $venvActivate = if ($env:OS -like "*Windows*") { "..\venv\Scripts\Activate.ps1" } else { "..\venv\bin\activate" }
    
    if (Test-Path $venvDir) {
        Write-Message "Found virtual environment, activating..." "INFO"
        try {
            # Activate virtual environment
            & $venvActivate
            Write-Message "Virtual environment activated" "SUCCESS"
        } catch {
            Write-Message "Failed to activate virtual environment: $_" "ERROR"
        }
    } else {
        Write-Message "No virtual environment found, using system Python" "WARNING"
    }
    
    # Install requirements if needed
    if (Test-Path "requirements.txt") {
        Write-Message "Installing required packages..." "INFO"
        pip install -r requirements.txt
    }
    
    # Start Flask app in background
    Write-Message "Starting Flask application..." "INFO"
    $flaskJob = Start-Job -ScriptBlock {
        Set-Location $using:backendDir
        python run.py
    }
    
    # Wait for Flask to start
    Write-Message "Waiting for Flask server to start..." "INFO"
    $maxAttempts = 10
    $attempts = 0
    $started = $false
    
    while ($attempts -lt $maxAttempts -and -not $started) {
        $attempts++
        Start-Sleep -Seconds 2
        
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET -ErrorAction Stop
            if ($response.status -eq "ok") {
                $started = $true
                Write-Message "Flask server started successfully!" "SUCCESS"
            }
        } catch {
            Write-Message "Waiting for Flask server (attempt $attempts of $maxAttempts)..." "INFO"
        }
    }
    
    if (-not $started) {
        Write-Message "Failed to start Flask server after $maxAttempts attempts" "ERROR"
        if ($flaskJob) {
            Stop-Job -Job $flaskJob
            Remove-Job -Job $flaskJob
        }
        exit 1
    }
    
    # Return to original directory
    Set-Location ".."
}

# Open the authentication tester in browser
$authTesterFile = ".\auth-tester.html"
if (Test-Path $authTesterFile) {
    Write-Message "Opening Authentication Tester in browser..." "INFO"
    Start-Process $authTesterFile
} else {
    Write-Message "Authentication Tester HTML file not found at $authTesterFile" "WARNING"
}

# Run the authentication test script
Write-Message "Running authentication test script..." "INFO"
python auth_test.py

# Ask user if they want to keep the server running
$keepRunning = Read-Host "`nKeep the Flask server running? (Y/N)"
if ($keepRunning -notmatch "^[Yy]") {
    if ($flaskJob) {
        Write-Message "Stopping Flask server..." "INFO"
        Stop-Job -Job $flaskJob
        Remove-Job -Job $flaskJob
        Write-Message "Flask server stopped" "SUCCESS"
    } else {
        Write-Message "Flask server was already running, not stopping it" "INFO"
    }
}

Write-Host "`n==== TEST COMPLETE ====`n" -ForegroundColor $INFO
