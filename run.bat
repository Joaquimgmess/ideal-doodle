@echo off
setlocal

echo ===================================
echo  Consolida API - EMERGENCIAS JF
echo ===================================

REM subir banco
echo Starting database...
docker compose up -d db

REM build api se necessario
echo Building API container...
docker compose build api

REM subir api com logs?

choice /c YN /n /t 5 /d N /m "Exibir logs da API? (Y/N) [default=N]: "

if errorlevel 2 goto nologs
if errorlevel 1 goto logs

:logs
echo Starting API with logs...
docker compose up api
goto end

:nologs
echo Starting API in background...
docker compose up -d api
goto end

:end
endlocal
