FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 bot \
    && useradd --uid 10001 --gid bot --create-home --shell /usr/sbin/nologin bot

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=bot:bot . .
RUN mkdir -p /app/data /app/logs \
    && chown -R bot:bot /app

USER 10001:10001

CMD ["python", "main.py"]
