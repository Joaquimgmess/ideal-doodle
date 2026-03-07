@echo off

if "%1"=="" goto help

if "%1"=="add" goto add
if "%1"=="up" goto up
if "%1"=="run" goto up
if "%1"=="down" goto down
if "%1"=="reset" goto reset

goto help

:add
if "%2"=="" (
echo Informe o nome da migration
echo Exemplo: migrate add create_user_table
exit /b 1
)

echo Criando migration "%2"...
uv run alembic revision --autogenerate -m "%2"
exit /b

:up
echo Aplicando migrations...
uv run alembic upgrade head
exit /b

:down
echo Revertendo ultima migration...
uv run alembic downgrade -1
exit /b

:reset
echo Resetando banco...
uv run alembic downgrade base
uv run alembic upgrade head
exit /b

:help
echo.
echo Comandos disponiveis:
echo.
echo migrate add NOME     - cria migration
echo migrate up           - aplica migrations
echo migrate down         - volta uma migration
echo migrate reset        - recria todas migrations
echo.
exit /b
