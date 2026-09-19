FROM python:3.12-slim@sha256:d764629ce0ddd8c71fd371e9901efb324a95789d2315a47db7e4d27e78f1b0e9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/azure-cost-api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/azure-cost-api/app ./app
COPY docs/api/azure-cost-query.openapi.json ./docs/api/azure-cost-query.openapi.json
COPY docs/api/azure-cost-query-mapping.json ./docs/api/azure-cost-query-mapping.json
COPY fixtures/azure-cost/EA-Cost-Actual.sample.csv ./fixtures/azure-cost/EA-Cost-Actual.sample.csv

RUN useradd --create-home --uid 10001 azureapi

ENV AZURE_COST_DATASET_PATH=/app/fixtures/azure-cost/EA-Cost-Actual.sample.csv
ENV AZURE_COST_MAPPING_PATH=/app/docs/api/azure-cost-query-mapping.json
ENV AZURE_COST_OPENAPI_PATH=/app/docs/api/azure-cost-query.openapi.json

EXPOSE 8002

USER azureapi

HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health').read()"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
