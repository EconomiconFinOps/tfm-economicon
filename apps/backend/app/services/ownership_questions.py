"""Ownership answers from billing v2, with no LLM inference or currency conversion."""
import hashlib
import json
import unicodedata
from datetime import datetime, timezone

from app.schemas.billing import BillingSummary
from app.schemas.ownership import OwnershipSelection


class OwnershipResultTooLarge(ValueError):
    pass


def display_label(value: str) -> str:
    # Labels originate in ingestion, not only in validated query input. Quote
    # them on one line so data cannot impersonate a financial response sentence.
    quoted = json.dumps(value, ensure_ascii=False)
    return "".join(f"\\u{ord(c):04x}" if unicodedata.category(c).startswith("C") or unicodedata.category(c) in {"Zl", "Zp"}
                   else c for c in quoted)


class OwnershipQuestionService:
    def answer(self, database, tenant_id: str, selection: OwnershipSelection) -> dict:
        start, end = selection.start_date, selection.end_date
        if start is None:
            start = datetime.now(timezone.utc).date().replace(day=1)
            end = (start.replace(year=start.year + 1, month=1) if start.month == 12
                   else start.replace(month=start.month + 1))
        resolved = selection.model_dump(mode="json") | {
            "start_date": start.isoformat(), "end_date": end.isoformat(),
        }
        tag_key = (selection.tag_key if selection.group_by == "tag" else
                   None if selection.group_by == "project" else selection.group_by)
        raw = database.fetch_billing_summary(
            tenant_id, start_date=start, end_date=end,
            group_by="project" if selection.group_by == "project" else "tag",
            tag_key=tag_key, include_provenance=True,
        )
        summary = BillingSummary.model_validate(raw).model_dump(mode="json")
        # Billing project/tag returns one group per value and currency. Never
        # sum rounded groups: unfiltered totals come directly from raw SQL sums.
        period_totals = [g for g in summary["totals"]
                         if selection.currency is None or g["currency"] == selection.currency]
        groups = [g for g in summary["groups"]
                  if selection.currency is None or g["currency"] == selection.currency]
        missing = [g for g in groups if g["value"] is None]
        identified = [g for g in groups if g["value"] is not None]
        selected_groups = [g for g in groups if selection.value is None or g["value"] == selection.value]
        selected_totals = (period_totals if selection.value is None else
                           [{k: g[k] for k in ("currency", "cost", "record_count")}
                            for g in selected_groups])
        reason = None
        if not summary["totals"]:
            status, reason = "no_data", "empty_period"
        elif not period_totals:
            status, reason = "no_data", "currency_not_found"
        elif not identified:
            status, reason = "insufficient_data", "dimension_unobserved"
            selected_totals = []
        elif not selected_groups:
            status, reason = "no_data", "value_not_found"
        else:
            status = "partial" if missing or summary["excluded_undated_count"] else "ok"

        payload = {
            "adapter_version": "ownership-1.0", "selection": resolved, "summary": summary,
            "selected_groups": selected_groups, "selected_totals": selected_totals,
            "missing_groups": missing, "provenance": raw["provenance"],
            "status": status, "reason": reason,
            "limitations": [
                "Observed labels are not validated against an ownership catalog.",
                "Source capability and freshness are unknown; records do not prove complete coverage.",
                "Missing-dimension counts cover the tenant period; undated counts cover the tenant across all dates.",
            ],
        }
        encoded = json.dumps({"tenant": tenant_id, **payload}, sort_keys=True,
                             separators=(",", ":"), ensure_ascii=False).encode()
        if len(summary["groups"]) > 1000 or len(encoded) > 262144:
            raise OwnershipResultTooLarge()
        evidence_id = "cost:" + hashlib.sha256(encoded).hexdigest()
        labels = {"project": "proyecto", "application": "aplicación", "owner": "equipo (owner)",
                  "cost_center": "centro de coste", "tag": f"etiqueta {tag_key}"}
        label = labels[selection.group_by]
        lines = [f"Coste registrado por {label}: {display_label(selection.value) if selection.value is not None else 'todos los valores'}.",
                 f"Periodo UTC: {start.isoformat()} a {end.isoformat()} (fin excluido)."]
        if reason == "empty_period":
            lines.append("No hay registros completados en el periodo; no equivale a gasto cero.")
        elif reason == "currency_not_found":
            lines.append(f"No hay registros para la moneda {selection.currency}; no equivale a gasto cero.")
        elif reason == "dimension_unobserved":
            lines.append(f"Datos insuficientes: ningún registro de la selección tiene {label}. La disponibilidad de esta dimensión en la fuente es desconocida.")
        elif reason == "value_not_found":
            lines.append("No se encontró ese valor exacto; no equivale a gasto cero.")
        else:
            lines.extend(f"Gasto de la selección: {g['cost']} {g['currency']} ({g['record_count']} registros)."
                         for g in selected_totals)
        if selection.value is not None or reason == "dimension_unobserved":
            lines.extend(f"Contexto del periodo, todos los valores: {g['cost']} {g['currency']} ({g['record_count']} registros)."
                         for g in period_totals)
        if selection.value is None and identified:
            lines.append(f"Desglose por {label}:")
            lines.extend(f"- {display_label(g['value'])}: {g['cost']} {g['currency']} ({g['record_count']} registros)."
                         for g in identified[:20])
            if len(identified) > 20:
                lines.append("Se muestran los primeros 20 grupos; el resto está en la evidencia guardada.")
        lines.extend(f"Sin {label} en el periodo: {g['cost']} {g['currency']} ({g['record_count']} registros)."
                     for g in missing)
        if summary["excluded_undated_count"]:
            lines.append(f"Excluidos {summary['excluded_undated_count']} registros sin fecha del tenant (todas las fechas; no atribuibles al periodo).")
        lines.append("Monedas separadas, sin conversión. Valores literales, sensibles a mayúsculas; no acreditan ownership ni validez de catálogo.")
        lines.append("Fuente: ingestas Azure completadas; la presencia de datos no garantiza cobertura completa ni actualidad. No se infiere aplicación de proyecto ni equipo de organización.")
        lines.append(f"Evidencia: {evidence_id}.")
        return {"content": "\n".join(lines), "cost_evidence": {
            "schema_version": "1.0", "id": evidence_id,
            "source": "azure_cost_records/completed", "data_environment": "unknown",
            "queried_at": datetime.now(timezone.utc).isoformat(), **payload,
        }}
