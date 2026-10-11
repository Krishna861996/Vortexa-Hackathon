FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --chmod=0444 entrypoint.py /app/entrypoint.py
USER 65534:65534
ENTRYPOINT ["python", "-I", "-B", "/app/entrypoint.py"]
