Write-Host "=== Starting MBTA Agntcy System ===" -ForegroundColor Cyan

# Load .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
    Write-Host "Loaded environment variables from .env" -ForegroundColor Green
}

$env:OPENAI_API_KEY = ""

# Check API key
if (-not $env:OPENAI_API_KEY) {
    Write-Host "ERROR: OPENAI_API_KEY not set!" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
Write-Host "
Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "  OK Docker is running" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Start observability stack
Write-Host "
Starting observability stack..." -ForegroundColor Yellow
docker-compose -f docker-compose-observability.yml up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK Observability stack started" -ForegroundColor Green
    Write-Host "     - ClickHouse: http://localhost:8123" -ForegroundColor Gray
    Write-Host "     - Jaeger:     http://localhost:16686" -ForegroundColor Gray
    Write-Host "     - Grafana:    http://localhost:3001" -ForegroundColor Gray
} else {
    Write-Host "  WARNING: Observability stack may have issues" -ForegroundColor Yellow
    Write-Host "  System will continue but observability may not work" -ForegroundColor Yellow
}

Start-Sleep -Seconds 8

# Save API key for terminals
$apiKey = $env:OPENAI_API_KEY

# Start Python services
Write-Host "
Starting Python services..." -ForegroundColor Yellow

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $env:OPENAI_API_KEY='$apiKey'; $host.UI.RawUI.WindowTitle = 'Exchange Agent (8100)'; python -m uvicorn src.exchange_agent.exchange_server:app --host 0.0.0.0 --port 8100 --reload"
Write-Host "  OK Exchange Agent (8100) with StateGraph" -ForegroundColor Green
Start-Sleep -Seconds 3

#Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $env:OPENAI_API_KEY='$apiKey'; $host.UI.RawUI.WindowTitle = 'Orchestrator (8101)'; python -m uvicorn src.orchestrator.mbta_server:app --host 0.0.0.0 --port 8101 --reload"
#Write-Host "  OK Orchestrator (8101)" -ForegroundColor Green
#Start-Sleep -Seconds 3

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $host.UI.RawUI.WindowTitle = 'Alerts Agent (8001)'; python -m uvicorn src.agents.alerts.main:app --host 0.0.0.0 --port 8001 --reload"
Write-Host "  OK Alerts Agent (8001)" -ForegroundColor Green
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $host.UI.RawUI.WindowTitle = 'Planner Agent (8002)'; python -m uvicorn src.agents.planner.main:app --host 0.0.0.0 --port 8002 --reload"
Write-Host "  OK Planner Agent (8002)" -ForegroundColor Green
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $host.UI.RawUI.WindowTitle = 'StopFinder Agent (8003)'; python -m uvicorn src.agents.stopfinder.main:app --host 0.0.0.0 --port 8003 --reload"
Write-Host "  OK StopFinder Agent (8003)" -ForegroundColor Green
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; $host.UI.RawUI.WindowTitle = 'Frontend UI (3000)'; python -m uvicorn src.frontend.chat_server:app --host 0.0.0.0 --port 3000 --reload"
Write-Host "  OK Frontend UI (3000)" -ForegroundColor Green

Write-Host "
Waiting for services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "
=====================================================================" -ForegroundColor Green
Write-Host "SUCCESS! MBTA System Started" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "
Endpoints:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Chat API:  http://localhost:8100/chat" -ForegroundColor White
Write-Host "  Jaeger:    http://localhost:16686" -ForegroundColor White
Write-Host "  Grafana:   http://localhost:3001 (admin/admin)" -ForegroundColor White
Write-Host "
To Stop: .\stop-mbta.ps1" -ForegroundColor Yellow
