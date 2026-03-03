FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project
COPY app ./app
COPY scripts ./scripts
COPY alembic.ini ./
RUN uv sync --no-dev
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["bash", "-c", "bash scripts/prestart.sh && fastapi run app/main.py --port 8000 --host 0.0.0.0"]
