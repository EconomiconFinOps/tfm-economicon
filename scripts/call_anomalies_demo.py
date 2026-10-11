"""Llama a POST /billing/anomalies/evaluate con la peticion de referencia de la demo y muestra el resultado.

Los datos son sinteticos (scripts/synthetic_anomalies.py): no son facturas de Azure ni vienen del dataset publico.
Se ejecuta dentro del contenedor del backend, que ya tiene DEMO_PASSWORD en su entorno; la contrasena y el token
no se imprimen nunca:

    docker compose -p jup107b exec -T backend python - < scripts/call_anomalies_demo.py
"""
import json
import os
import urllib.error
import urllib.request

BASE = "http://localhost:8000"
TENANT = "tenant-core"
RULES = {"absolute_threshold": "2000.00", "deviation_threshold_percent": "50.00", "min_absolute_increase": "100.00"}
REQUEST = {"start_date": "2026-09-08", "end_date": "2026-09-15", "group_by": "service", "currency": "EUR", **RULES}


def call(method, path, body=None, token=None, tenant=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if tenant:
        headers["X-Tenant-Id"] = tenant
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        return error.code, None


status, session = call("POST", "/auth/login", {"email": "operator@example.com", "password": os.environ["DEMO_PASSWORD"]})
assert status == 200, f"login: HTTP {status}"
token = session["access_token"]

status, result = call("POST", "/billing/anomalies/evaluate", REQUEST, token, TENANT)
assert status == 200, f"evaluate: HTTP {status}"
print("DATOS SINTETICOS - no son facturas de Azure ni del dataset publico")
print("HTTP", status, "| estado", result["evaluation_status"],
      "| base desde", result["baseline_period"]["start_date"], "| actual desde", result["current_period"]["start_date"])
for item in result["assessments"]:
    print(f'{item["group_value"]:<10} actual {item["current_cost"]:>8} base {str(item["baseline_cost"]):>8} '
          f'delta {str(item["delta_amount"]):>8} % {str(item["deviation_percent"]):>7} '
          f'{item["threshold_status"]:<9} {item["deviation_status"]:<21} {item["trigger_reasons"]}')
print("ALERTAS:", [alert["group_value"] for alert in result["alerts"]])
