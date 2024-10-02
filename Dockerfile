FROM python:3.12.7-alpine3.20@sha256:e75de178bc15e72f3f16bf75a6b484e33d39a456f03fc771a2b3abb9146b75f8

WORKDIR /inventory-management-system-api-run

COPY pyproject.toml ./
COPY inventory_management_system_api/ inventory_management_system_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    python3 -m pip install .;

CMD ["fastapi", "dev", "inventory_management_system_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
EXPOSE 8000
