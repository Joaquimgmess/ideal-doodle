@echo off
setlocal EnableDelayedExpansion

echo =====================================
echo        GIT FLOW AUTOMATIZADO
echo =====================================
echo.

:: ------------------------------------------------
:: Detecta main ou master
:: ------------------------------------------------
git show-ref --verify --quiet refs/heads/main
IF %ERRORLEVEL% EQU 0 (
    set MAIN_BRANCH=main
) ELSE (
    set MAIN_BRANCH=master
)

echo Branch principal detectada: %MAIN_BRANCH%
echo.

:: ------------------------------------------------
:: Verifica se upstream existe
:: ------------------------------------------------
git remote get-url upstream >nul 2>&1
IF ERRORLEVEL 1 (
    echo Remote 'upstream' nao configurado.
    echo.
    echo Informe a URL do upstream ou pressione ENTER para ignorar
    echo Exemplo: https://github.com/org/repositorio.git
    echo.

    set /p UPSTREAM_URL="Upstream URL: "

    if not "!UPSTREAM_URL!"=="" (
        echo Adicionando upstream...
        git remote add upstream !UPSTREAM_URL!
    ) else (
        echo Upstream ignorado.
    )

    echo.
)

:: ------------------------------------------------
:: Atualiza branch principal
:: ------------------------------------------------
echo Atualizando %MAIN_BRANCH%...

git checkout %MAIN_BRANCH%

git remote get-url upstream >nul 2>&1
IF ERRORLEVEL 1 (
    git pull origin %MAIN_BRANCH%
) ELSE (
    git pull upstream %MAIN_BRANCH%
)

echo.

:: ------------------------------------------------
:: Escolher tipo de branch
:: ------------------------------------------------
echo Escolha o tipo de branch:
echo.
echo F - FEATURE (nova funcionalidade)
echo X - FIX (correcao de bug)
echo H - HOTFIX (correcao urgente)
echo.

set /p TYPE_OPTION="Opcao: "

if "%TYPE_OPTION%"=="F" set PREFIX=feature
if "%TYPE_OPTION%"=="X" set PREFIX=fix
if "%TYPE_OPTION%"=="H" set PREFIX=hotfix
if "%TYPE_OPTION%"=="f" set PREFIX=feature
if "%TYPE_OPTION%"=="x" set PREFIX=fix
if "%TYPE_OPTION%"=="h" set PREFIX=hotfix

if "%PREFIX%"=="" (
    echo Opcao invalida.
    exit /b 1
)

echo.

:: ------------------------------------------------
:: Nome da branch
:: ------------------------------------------------
echo  Informe o nome da branch
echo  Exemplo: "cadastro-usuario"
echo  o esultado final sera algo como %PREFIX%/cadastro-usuario
echo.

set /p BRANCH_NAME="Nome: "

if "%BRANCH_NAME%"=="" (
    echo Nome da branch nao pode ser vazio.
    exit /b 1
)

set FINAL_BRANCH=%PREFIX%/%BRANCH_NAME%

echo.
echo Criando branch: %FINAL_BRANCH%
echo.

:: ------------------------------------------------
:: Criar branch
:: ------------------------------------------------
git checkout -b %FINAL_BRANCH%

:: ------------------------------------------------
:: Push
:: ------------------------------------------------
echo.
echo Enviando para origin...
git push -u origin %FINAL_BRANCH%

echo.
echo =====================================
echo Branch criada com sucesso!
echo Apos conclusao git add . e send "feature alguma coisa"
echo %FINAL_BRANCH%
echo =====================================

pause
