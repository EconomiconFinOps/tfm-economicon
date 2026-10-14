import { useEffect, useMemo, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { severityLabels, statusLabels } from "../lib/anomalyPanel";
import { fetchAnomalyEpisodes } from "../services/api";
import { isAnomalyEpisodeId } from "../services/contracts";

const fieldClass = "rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-highlight";

// Campos del modo «Explicar una anomalia» (JUP-038, design.md decisiones 9 y 10).
//
// Este componente SOLO se monta con el modo activo: asi la lista de anomalias no se pide nunca con el
// modo apagado (alternativa descartada: montarlo siempre y confiar en `enabled`, que deja la decision
// repartida entre dos archivos y es facil de romper sin que ninguna prueba lo note).
//
// `linkedId` es el parametro `?episode=` de la direccion. Es un dato NO fiable (cualquiera puede editar
// la URL o traerla de otro cliente): no autoriza nada, solo PRESELECCIONA si el id esta entre las
// anomalias que este mismo cliente acaba de devolver. El backend vuelve a filtrar por cliente al enviar.
export function AnomalyExplanationFields({ token, tenantId, selected, onSelect, linkedId, disabled }: {
  token: string; tenantId: string; selected: string; onSelect: (episodeId: string) => void;
  linkedId: string; disabled: boolean;
}) {
  const query = useQuery({
    // Clave propia por cliente: la lista de un cliente nunca se sirve a otro.
    queryKey: ["anomaly-episodes-for-explanation", tenantId],
    queryFn: ({ signal }) => fetchAnomalyEpisodes(token, tenantId, signal),
    enabled: Boolean(token && tenantId),
    // Sin reintentos, como el panel de anomalias: un fallo se ve enseguida en vez de tras varios intentos.
    retry: false
  });

  // Solo se ofrecen ids con el formato exacto del contrato. Un id de otro formato (o con salto de linea
  // final) no podria enviarse sin un 422 del servidor, asi que ni se muestra: no quedan opciones huerfanas.
  // El orden es el del backend; ordenar en el cliente duplicaria una regla que ya decide el servidor.
  const options = useMemo(
    () => query.data?.episodes.filter((item) => isAnomalyEpisodeId(item.id)),
    [query.data]
  );

  // La preseleccion del enlace se aplica una sola vez, cuando llega la primera lista. Con una referencia
  // y no con estado derivado, para que si la persona vuelve a «Elige una anomalia» no se le reimponga.
  const linkApplied = useRef(false);
  useEffect(() => {
    if (!options || linkApplied.current) return;
    linkApplied.current = true;
    if (linkedId && options.some((item) => item.id === linkedId)) onSelect(linkedId);
  }, [options, linkedId, onSelect]);

  if (query.isPending) return <p className="text-sm text-muted-foreground">Cargando anomalías...</p>;
  // Texto fijo y no `error.message`: el cuerpo de la respuesta es del servidor y no debe llegar a pantalla.
  if (query.isError || !options) return <p className="text-sm text-danger" role="alert">No se han podido cargar las anomalías.</p>;

  // El aviso solo existe con la lista ya cargada: antes no se sabe si el id es de este cliente y avisar
  // seria falso. Es informativo (`status`), no un fallo de la peticion (`alert`).
  const linkedMissing = linkedId !== "" && !options.some((item) => item.id === linkedId);
  return <div className="flex flex-col gap-2">
    {linkedMissing && <p className="text-sm text-muted-foreground" role="status">La anomalía indicada en el enlace no está entre las de este cliente.</p>}
    {options.length === 0
      ? <p className="text-sm text-muted-foreground">Este cliente no tiene anomalías guardadas. Se detectan desde el panel de Anomalías.</p>
      : <label className="flex flex-col gap-1 text-sm">Anomalía
        <select className={fieldClass} value={selected} disabled={disabled} onChange={(event) => onSelect(event.target.value)}>
          <option value="">Elige una anomalía</option>
          {options.map((item) => <option key={item.id} value={item.id}>
            {`${item.service ?? "(sin servicio)"} · ${item.currency} · desde ${item.start_date} · ${severityLabels[item.severity]} · ${statusLabels[item.status]}`}
          </option>)}
        </select>
      </label>}
  </div>;
}
