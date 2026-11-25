# DAKSHU AI: Local Model Setup & Ollama Modelfile Compiler
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  🌸 DAKSHU AI: Local Model Setup & Ollama Compiler  " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Verify Ollama CLI or AppData Path
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
$ollamaDefaultPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"

if (-not $ollamaCmd -and -not (Test-Path $ollamaDefaultPath)) {
    Write-Host "`n[!] Ollama is not installed on your computer yet." -ForegroundColor Red
    Write-Host "    Ollama is the local AI engine required to run the model without API keys." -ForegroundColor Yellow
    Write-Host "`nOpening the official Ollama download link in your browser..." -ForegroundColor Green
    Start-Process "https://ollama.com/download/OllamaSetup.exe"
    Write-Host "`nSteps to complete:" -ForegroundColor Cyan
    Write-Host "1. Run the downloaded 'OllamaSetup.exe' (takes ~30 seconds)."
    Write-Host "2. Once installed, run this script again!"
    Write-Host "`nPress any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Exit
}

$ollamaBin = if ($ollamaCmd) { "ollama" } else { $ollamaDefaultPath }

# 2. Check if Ollama daemon is running
try {
    $null = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[✓] Ollama daemon is running on http://localhost:11434" -ForegroundColor Green
} catch {
    Write-Host "[*] Starting Ollama background service..." -ForegroundColor Yellow
    Start-Process $ollamaBin -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 4
}

# 3. Pull base Gemma 2 2B model
Write-Host "`n[1/2] Pulling Google Gemma 2 (2B) base model (approx 1.6 GB)..." -ForegroundColor Cyan
& $ollamaBin pull gemma2:2b

# 4. Compile Dakshu Persona & Hyperparameters from Modelfile
$modelfilePath = Join-Path $PSScriptRoot "Modelfile"
Write-Host "`n[2/2] Compiling 'dakshu' custom companion model from $modelfilePath..." -ForegroundColor Cyan
& $ollamaBin create dakshu -f $modelfilePath

Write-Host "`n======================================================" -ForegroundColor Green
Write-Host "  ✅ 'dakshu' Local Model Successfully Compiled!       " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "• Test directly in terminal: ollama run dakshu" -ForegroundColor Magenta
Write-Host "• DAKSHU AI backend is configured to use 'dakshu' automatically." -ForegroundColor Cyan
Write-Host "• Run 'uvicorn backend.main:app --reload' to start your app!" -ForegroundColor Green
