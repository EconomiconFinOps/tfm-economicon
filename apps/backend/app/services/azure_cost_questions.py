"""Deterministic answers from ingested costs; no model or external Azure call."""
import hashlib
import json
from datetime import datetime, timezone

from app.schemas.assistant import AzureCostSelection
from app.schemas.billing import BillingSummary


class AzureCostQuestionService:
    def answer(self, database, tenant_id: str, selection: AzureCostSelection) -> dict:
        start, end = selection.start_date, selection.end_date
        if start is None:
            start = datetime.now(timezone.utc).date().replace(day=1)
            end = (start.replace(year=start.year + 1, month=1) if start.month == 12
                   else start.replace(month=start.month + 1))
        resolved = selection.model_dump(mode="json") | {
            "start_date": start.isoformat(), "end_date": end.isoformat(),
        }
        raw = database.fetch_billing_summary(
            tenant_id, start_date=start, end_date=end, group_by=selection.group_by,
            selected_subscription=selection.subscription_id, selected_value=selection.value,
            include_provenance=True,
        )
        summary = BillingSummary.model_validate(raw).model_dump(mode="json")
        provenance = raw["provenance"]
        evidence_payload = {"selection": resolved, "summary": summary, "provenance": provenance}
        evidence_id = "cost:" + hashlib.sha256(json.dumps(
            {"tenant": tenant_id, **evidence_payload}, sort_keys=True,
            separators=(",", ":"), ensure_ascii=False,
        ).encode()).hexdigest()
        status = ("no_data" if not summary["totals"] else
                  "partial" if summary["data_status"] == "partial" else "ok")
        labels = {"subscription": "suscripción", "account": "cuenta de facturación", "service": "servicio"}
        scope = f"{labels[selection.group_by]}: {selection.value or 'todos los valores'}"
        if selection.subscription_id:
            scope += f"; suscripción: {selection.subscription_id}"
        lines = [f"Coste real Azure simulado — {scope}.",
                 f"Periodo UTC: {start.isoformat()} a {end.isoformat()} (fin excluido)."]
        if not summary["totals"]:
            lines.append("No hay registros de coste completados para esta selección; no equivale a gasto cero.")
        else:
            lines.extend(f"Gasto registrado: {item['cost']} {item['currency']} ({item['record_count']} registros)."
                         for item in summary["totals"])
        if selection.value is None and summary["groups"]:
            lines.append(f"Desglose por {labels[selection.group_by]}:")
            for group in summary["groups"][:20]:
                lines.append(f"- {group['value'] if group['value'] is not None else '(sin valor)'}: {group['cost']} {group['currency']} ({group['record_count']} registros).")
            if len(summary["groups"]) > 20:
                lines.append("Se muestran los primeros 20 grupos; el desglose completo se conserva en la evidencia.")
        if len(summary["totals"]) > 1:
            lines.append("Las monedas se muestran por separado; no se han convertido ni sumado entre sí.")
        if summary["missing_dimension_count"]:
            lines.append(f"Datos parciales: {summary['missing_dimension_count']} registros sin {labels[selection.group_by]}.")
        if summary["excluded_undated_count"]:
            lines.append(f"Excluidos {summary['excluded_undated_count']} registros sin fecha del ámbito de suscripción.")
        if provenance["observed_day_count"]:
            lines.append(f"Días con datos: {provenance['observed_day_count']}; último día observado: {provenance['last_usage_date']}.")
        if provenance["ingestion_ids"]:
            lines.append("Ingestas de origen: " + ", ".join(provenance["ingestion_ids"][:20]) +
                         (" (primeras 20; lista completa en evidencia)." if len(provenance["ingestion_ids"]) > 20 else "."))
        lines.append("Fuente: ingestas Azure completadas. La presencia de registros no garantiza cobertura completa del periodo ni datos actualizados.")
        lines.append(f"Evidencia: {evidence_id}.")
        return {"content": "\n".join(lines), "citations": [], "cost_evidence": {
            "schema_version": "1.0", "id": evidence_id, "status": status,
            "source": "azure_cost_records/completed", "data_environment": "simulated",
            "queried_at": datetime.now(timezone.utc).isoformat(), **evidence_payload,
        }}
