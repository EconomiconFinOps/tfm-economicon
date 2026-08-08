# Fixtures Azure Cost

Muestras deterministas generadas desde `dataset-examples.zip` de Microsoft
FinOps Toolkit v14. No son una copia aleatoria manual: pueden regenerarse con el
comando documentado en `docs/data/azure-sample-dataset.md`.

- `EA-Cost-Actual.sample.csv` es la entrada predeterminada para JUP-073.
- Cada fichero contiene como máximo 50 filas, más la cabecera.
- Correos, GUID e identificadores numéricos se seudonimizan de forma estable.
- `manifest.json` registra el checksum de origen y la cantidad de filas.
- `LICENSE.microsoft-finops-toolkit.txt` conserva el aviso MIT de Microsoft.
- El ZIP original no debe añadirse al repositorio.

Estos datos siguen conteniendo nombres y etiquetas sintéticos de Microsoft y
solo deben utilizarse en desarrollo y pruebas.
