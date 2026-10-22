FROM python:3.12-slim@sha256:d764629ce0ddd8c71fd371e9901efb324a95789d2315a47db7e4d27e78f1b0e9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV EMBEDDING_TOKENIZER_FILE=/opt/economicon/tokenizers/cl100k_base.tiktoken

RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng libseccomp2 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.lock requirements-chat.lock requirements-documents.lock requirements-documents.txt requirements-chunking.lock requirements-chunking.txt requirements-aws.txt requirements-aws.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock -r requirements-chat.lock -r requirements-documents.lock -r requirements-chunking.lock -r requirements-aws.lock \
    && pip check \
    && pip install --dry-run --no-index -r requirements.txt

COPY app ./app
COPY build_tokenizer.py /tmp/build_tokenizer.py
RUN PYTHONPATH=/app python /tmp/build_tokenizer.py --output /app/app/agents/prompt_resources/jup035/chat/v4/tokenizer.json --legacy-output /app/app/agents/prompt_resources/jup035/chat/v2/tokenizer.json --embedding-output /opt/economicon/tokenizers/cl100k_base.tiktoken
RUN python -c "from app.core.chat_resources import load_resources; from app.core.summary_resources import load_resources as summary; load_resources(); summary()"
RUN find /app/app -type d -exec chmod 755 {} +

RUN useradd --create-home --uid 10001 economicon \
    && rm -f /tmp/build_tokenizer.py \
    && chown economicon:economicon /tmp && chmod 0700 /tmp
VOLUME ["/tmp"]

EXPOSE 8001

USER economicon

HEALTHCHECK --interval=15s --timeout=5s --retries=10 --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()"

CMD ["python", "-m", "app.run_all"]
