
$envFile = Join-Path $PSScriptRoot ".env"

if (Test-Path $envFile) {
    Write-Host "Loading environment variables from .env file..." -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
} else {
    Write-Host "Warning: .env file not found. Using default values or system environment variables." -ForegroundColor Yellow
    $env:GROQ_API_KEY=""
    $env:N8N_UPLOAD_URL=""
    $env:N8N_WEBHOOK_URL=""
    $env:N8N_SEARCH_URL=""
}

Set-Location $PSScriptRoot

Write-Host "Starting Flask app..." -ForegroundColor Green
python app.py

