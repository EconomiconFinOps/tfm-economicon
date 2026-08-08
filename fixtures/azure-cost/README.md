# Fixtures Azure Cost

Muestras deterministas generadas desde `dataset-examples.zip` de Microsoft
FinOps Toolkit v14. No son una copia aleatoria manual: pueden regenerarse con el
comando documentado en `docs/data/azure-sample-dataset.md`.

- `EA-Cost-Actual.sample.csv` es la entrada predeterminada para JUP-073.
- Cada fichero contiene como máximo 50 filas, más la cabecera.
- Las filas conservan sin modificaciones los valores públicos de Microsoft.
- `manifest.json` registra el checksum de origen y la cantidad de filas.
- `LICENSE.microsoft-finops-toolkit.txt` conserva el aviso MIT de Microsoft.
- El ZIP original no debe añadirse al repositorio.

Son datos públicos de ejemplo y deben utilizarse en desarrollo y pruebas.
