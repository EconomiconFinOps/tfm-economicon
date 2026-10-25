"""Estimación offline. Python 3.10+, biblioteca estándar, sin acceso AWS/red.

Ejecutar: python docs/planning/costes-aws/calcular.py
Escribe resultados.json y desglose.csv junto a este archivo.
Los volúmenes son hipótesis editables, nunca mediciones de capacidad.
"""
import csv
import json
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = json.loads((ROOT / "precios.json").read_text(encoding="utf-8"))
P = {k: D(v["usd"]) for k, v in INPUT["prices"].items()}
FX = D(INPUT["fx"]["usd_per_eur"])
MONTH = D(730)


def calculate(name, *, hours=730, ha=True, cycles=1, scale=1):
    """scale sólo modifica los volúmenes variables; hours es tiempo FACTURABLE total.

    Demo: tres ciclos independientes, control persistente todo el mes, 5 USD
    adicionales de reserva de residuos. La zona privada se cobra por ciclo.
    """
    h, s = D(str(hours)), D(str(scale))
    demo = h != MONTH
    rows = []

    def add(category, label, quantity, price):
        q = D(str(quantity))
        rate = P[price] if isinstance(price, str) else D(str(price))
        rows.append(dict(category=category, item=label, quantity=str(q),
                         usd_rate=str(rate), price_key=price if isinstance(price, str) else "assumption",
                         usd=q * rate))

    tasks, nat, mq_nodes = (6, 3, 3) if ha else (3, 1, 1)
    add("infra_fija", "Fargate vCPU", h * tasks / 2, "cpu")
    add("infra_fija", "Fargate GiB", h * tasks, "memory")
    add("infra_fija", "RDS dos bases (standby incluido en precio HA)", h * 2, "rds_ha" if ha else "rds_single")
    add("infra_fija", "RDS GP3 40 GB lógicos", 40 * h / MONTH, "rds_disk_ha" if ha else "rds_disk_single")
    add("infra_fija", "RabbitMQ cluster completo o broker único", h, "mq_ha" if ha else "mq_single")
    add("infra_fija", "RabbitMQ EBS 200 GB por nodo", 200 * mq_nodes * h / MONTH, "mq_disk")
    add("infra_fija", "NAT Gateway", nat * h, "nat")
    add("infra_fija", "IPv4 NAT", nat * h, "ipv4")
    add("infra_fija", "ALB interno", h, "alb")
    add("infra_fija", "WAF ACL", h / MONTH, "waf_acl")
    add("infra_fija", "WAF una regla", h / MONTH, "waf_rule")
    add("infra_fija", "Route53 pública persistente", 1, "zone")
    add("infra_fija", "Route53 privada (mes sin prorrateo por ciclo)", cycles, "zone")
    add("infra_fija", "Cloud Map registros processor y azure-cost-api", (4 if ha else 2) * h / MONTH, "cloudmap")
    add("infra_fija", "KMS una versión; demo reserva mes completo", 1, "key")
    add("infra_fija", "Secrets 6 runtime prorrateados + 2 control persistentes", 6 * h / MONTH + 2, "secret")
    add("datos_almacenados", "S3 app+control incluyendo versiones GB-mes", (20 if not demo else 2) * s, "s3_storage")
    add("datos_almacenados", "ECR retención 3 GB-mes", 3, "ecr")
    add("operacion_variable", "Logs ingeridos GB (incluye observabilidad ECS)", (10 if not demo else 1) * s, "log_ingest")
    add("operacion_variable", "Logs retenidos GB-mes", (5 if not demo else 1) * s, "log_storage")
    add("operacion_variable", "Métricas custom/Container Insights equivalentes", 60 * h / MONTH * s, "metric")
    add("operacion_variable", "Alarmas estándar", 3 * h / MONTH, "alarm")
    add("operacion_variable", "ALB 0.25 LCU promedio", h * D("0.25") * s, "lcu")
    add("operacion_variable", "Cognito Essentials MAU", (100 if not demo else 5) * s, "mau")
    add("operacion_variable", "DNS consultas", (1000000 if not demo else 10000) * s, "dns")
    add("operacion_variable", "Secrets API requests", (10000 if not demo else 1000) * s, "secret_request")
    add("operacion_variable", "KMS requests", (10000 if not demo else 1000) * s, "key_request")
    add("operacion_variable", "Reserva control DDB PITR/SNS/SQS/Scheduler y logs París USD", 1, 2)
    add("ingesta_variable", "S3 PUT/COPY/LIST operaciones", (10000 if not demo else 1000) * s, "s3_put")
    add("ingesta_variable", "S3 GET operaciones", (100000 if not demo else 10000) * s, "s3_get")
    add("red_variable", "CloudFront egress a Europa GB", (100 if not demo else 1) * s, "cf_egress")
    add("red_variable", "CloudFront HTTPS requests", (1000000 if not demo else 10000) * s, "cf_request")
    add("red_variable", "CloudFront Function (una por petición)", (1000000 if not demo else 10000) * s, "cf_function")
    add("red_variable", "WAF requests", (1000000 if not demo else 10000) * s, "waf_request")
    add("red_variable", "NAT GB procesados (incluye pulls/Bedrock)", (10 if not demo else 5) * s, "nat_gb")
    add("red_variable", "Reserva transferencia interAZ/interregión USD", 1, 1)
    # 4 despliegues mensuales o 3 ciclos demo; minutos TOTALES de todas las
    # acciones up/down y builds. No se multiplica por número de pipelines.
    runs = cycles if demo else 4
    add("cicd_variable", "CodeBuild minutos: 180 por ciclo up+down", runs * 180, "build")
    add("cicd_variable", "CodePipeline V2 action-minutes: 200 por ciclo", runs * 200, "pipeline")
    add("ia_variable", "Nova Micro entrada millones tokens agregados", (50 if not demo else 1) * s * 1000, "llm_input_1k")
    add("ia_variable", "Nova Micro salida millones tokens agregados", (5 if not demo else D("0.1")) * s * 1000, "llm_output_1k")
    add("ia_variable", "Titan V2 embeddings millones tokens", (10 if not demo else 1) * s * 1000, "embedding_1k")
    if demo:
        add("residuos_reserva", "Reserva adicional tras destroy USD (no límite)", 1, 5)
    totals = {}
    for row in rows:
        c = row["category"]
        totals[c] = totals.get(c, D(0)) + row["usd"]
    total = sum(totals.values(), D(0))
    return dict(name=name, hours=str(h), cycles=cycles, ha=ha, variable_scale=str(s),
                totals_usd={k: str(v) for k, v in totals.items()}, total_usd=str(total),
                total_eur=str(total / FX), total_eur_plus_20pct_contingency=str(total / FX * D("1.2")), rows=rows)


def main():
    scenarios = [calculate("referencia_ha_730h"), calculate("piloto_single_az_730h", ha=False)]
    scenarios += [calculate(f"referencia_ha_demanda_x{x}", scale=x) for x in (0.1, 10)]
    scenarios += [calculate(f"demo_3_ciclos_{h}h", hours=3 * h, cycles=3) for h in (2, 4, 8)]
    # Invariantes contra errores materiales de doble conteo y cambio monetario.
    base = scenarios[0]
    by_label = {r["item"]: r["usd"] for r in base["rows"]}
    assert by_label["RabbitMQ cluster completo o broker único"] == D("702.990")
    assert by_label["RabbitMQ EBS 200 GB por nodo"] == D("66.00")
    assert by_label["RDS dos bases (standby incluido en precio HA)"] == D("201.480")
    assert base["total_eur"] == str(D(base["total_usd"]) / FX)
    result = dict(date=INPUT["verified_date"], source_commit="8e879dae3f23d52f46ea2b625ca1f2eebd22cd4a",
                  assumptions="README.md", fx=INPUT["fx"], scenarios=scenarios)
    (ROOT / "resultados.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    with (ROOT / "desglose.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "category", "item", "quantity", "usd_rate", "price_key", "usd", "eur"])
        for case in scenarios:
            for r in case["rows"]:
                w.writerow([case["name"], r["category"], r["item"], r["quantity"], r["usd_rate"], r["price_key"], r["usd"], r["usd"] / FX])
    for case in scenarios:
        print(f'{case["name"]}: USD {D(case["total_usd"]):.2f}; EUR {D(case["total_eur"]):.2f} sin IVA')


if __name__ == "__main__":
    main()
