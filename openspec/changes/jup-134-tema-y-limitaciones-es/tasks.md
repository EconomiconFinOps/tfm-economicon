## 1. Selector de tema con el tema activo (frontend-brand-identity, D1)

- [ ] 1.1 Reescribir en `useTheme.test.tsx` los casos que dependen del texto fijo: con el tema claro el botón se llama «Tema claro» y con el oscuro «Tema oscuro»; las comprobaciones de `aria-pressed` pasan a comprobar el texto visible y la ausencia del atributo (Red)
- [ ] 1.2 Añadir casos en `useTheme.test.tsx`: el texto cambia al alternar sin recargar, una elección guardada fija el texto al volver a montar, el nombre accesible es exactamente el texto visible sin `aria-label`, el `title` describe la acción («Cambiar a tema oscuro» / «Cambiar a tema claro») y el icono sigue oculto a tecnologías de apoyo (Red)
- [ ] 1.3 Ajustar `brand-spec.guard.test.tsx` para buscar el conmutador por el nombre del tema activo en la prueba (Red)
- [ ] 1.4 Cambiar `ThemeToggle.tsx`: texto según `isDark`, sin `aria-pressed`, con `title` de la acción; sin tocar `useTheme` (Green)
- [ ] 1.5 Pruebas de mutación del componente y regresión del frontend (`corepack pnpm --filter frontend test`, lint y type-check) en verde

## 2. Limitaciones de los episodios en español (cost-anomaly-episodes, D2)

- [ ] 2.1 Añadir una prueba de backend de regresión: un episodio leído devuelve las cinco limitaciones en español, en orden, y ninguna de las cinco frases en inglés anteriores (Red)
- [ ] 2.2 Reescribir en `test_anomaly_explanations.py` la prueba de la pareja inglés/español para que exija que la explicación use la misma lista que el episodio (`LIMITATIONS`), conservando la redacción literal esperada (Red)
- [ ] 2.3 Pasar `LIMITATIONS` de `anomaly_episodes.py` a las cinco frases en español y hacer que `anomaly_explanations.py` la importe, eliminando `LIMITATIONS_ES` y actualizando su comentario (Green)
- [ ] 2.4 Comprobar que el texto del asistente, `anomaly_evidence.limitations` y la prueba de cambio de identificador por limitaciones siguen igual; pruebas de mutación sobre las listas y regresión del backend en verde

## 3. Documentación

- [ ] 3.1 Actualizar `apps/frontend/README.md` (botón que muestra el tema activo)
- [ ] 3.2 Actualizar `docs/continuidad/frontend-espanol.md`, `docs/continuidad/identidad-marca-frontend.md` y la fila de `docs/continuidad/README.md`, indicando que las limitaciones de episodios ya no son un valor de la API en inglés y el cambio de identificador de evidencia descrito en design.md

## 4. Comprobación final

- [ ] 4.1 Ver en el navegador (`docker compose up --build`, `/anomalias`) el texto del selector en claro, en oscuro y tras recargar, y el desplegable «Limitaciones» del detalle de una anomalía en español
- [ ] 4.2 `corepack pnpm lint`, `corepack pnpm build`, `corepack pnpm test`, `corepack pnpm openspec:validate` y `corepack pnpm jup:check -- --change jup-134-tema-y-limitaciones-es` en verde
