where uv >nul 2>nul || pip install uv
cd backend
uv lock
cd ..
docker compose up --build