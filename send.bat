@echo off
setlocal EnableDelayedExpansion

echo =====================================
echo             GIT SEND
echo =====================================
echo.

:: ------------------------------------------------
:: Verifica mensagem
:: ------------------------------------------------
if "%~1"=="" (
    echo Informe a mensagem do commit.
    echo Exemplo:
    echo send "feat: adiciona endpoint pedidos"
    exit /b 1
)

set COMMIT_MSG=%~1

:: ------------------------------------------------
:: Valida Conventional Commit
:: ------------------------------------------------
set VALID=0

for %%t in (feat fix refactor docs test chore perf build ci) do (
    echo %COMMIT_MSG% | findstr /b /c:"%%t:" >nul
    if !errorlevel! == 0 set VALID=1
)

if "!VALID!"=="0" (
    echo.
    echo ERRO: mensagem de commit fora do padrao.
    echo.
    echo Use Conventional Commits:
    echo.
    echo feat: nova funcionalidade
    echo fix: correcao de bug
    echo refactor: refatoracao
    echo docs: documentacao
    echo test: testes
    echo chore: tarefas internas
    echo perf: melhoria de performance
    echo build: build ou dependencias
    echo ci: integracao continua
    echo.
    echo Exemplo:
    echo send "feat: adiciona endpoint pedidos"
    exit /b 1
)

:: ------------------------------------------------
:: Detecta branch
:: ------------------------------------------------
for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i

echo Branch atual: %BRANCH%
echo.

:: ------------------------------------------------
:: Verifica staged files
:: ------------------------------------------------
git diff --cached --quiet

if %ERRORLEVEL% EQU 0 (
    echo Nenhum arquivo preparado para commit.
    echo.
    echo Execute antes:
    echo git add arquivo
    echo.
    exit /b 1
)

:: ------------------------------------------------
:: Commit
:: ------------------------------------------------
echo Criando commit...
git commit -m "%COMMIT_MSG%"

if errorlevel 1 exit /b 1

:: ------------------------------------------------
:: Pull
:: ------------------------------------------------
echo Sincronizando com origin...
git pull --rebase origin %BRANCH%

if errorlevel 1 (
    echo.
    echo ERRO no pull. Resolva conflitos antes.
    exit /b 1
)

:: ------------------------------------------------
:: Push
:: ------------------------------------------------
echo Enviando para origin...
git push origin %BRANCH%

echo.
echo =====================================
echo Commit enviado com sucesso!
echo =====================================

pause
