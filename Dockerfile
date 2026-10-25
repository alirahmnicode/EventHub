FROM python:3.13-slim

# Copy the uv binary from its official image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONPATH=/code

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /code

# 1. Install dependencies only (cached until pyproject.toml / uv.lock change)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 2. Copy the source code (keeps the `app` folder name)
COPY pyproject.toml uv.lock ./
COPY app ./app

EXPOSE 8000

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]