FROM python:3.12-slim

WORKDIR /app
COPY collaboration.py /app/collaboration.py

RUN useradd --create-home --uid 10001 collab \
    && mkdir -p /data/snapshots \
    && chown -R collab:collab /data

USER collab
ENTRYPOINT ["python", "/app/collaboration.py"]
CMD ["--help"]
