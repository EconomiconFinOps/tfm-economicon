FROM python:3.12-slim@sha256:d764629ce0ddd8c71fd371e9901efb324a95789d2315a47db7e4d27e78f1b0e9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.lock requirements-chat.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock -r requirements-chat.lock \
    && pip check \
    && pip install --dry-run --no-index -r requirements.txt

COPY app ./app
COPY build_tokenizer.py /tmp/build_tokenizer.py
RUN python /tmp/build_tokenizer.py --output /app/app/agents/prompt_resources/jup035/chat/v2/tokenizer.json
RUN python -c "from app.core.chat_resources import load_resources; from app.core.summary_resources import load_resources as summary; load_resources(); summary()"
RUN find /app/app -type d -exec chmod 755 {} +

RUN useradd --create-home --uid 10001 economicon

EXPOSE 8001

USER economicon

HEALTHCHECK --interval=15s --timeout=5s --retries=10 --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()"

CMD ["python", "-m", "app.run_all"]
