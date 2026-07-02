from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import os

# Fecha de ayer
hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
fecha = hoy - timedelta(days=1)

fecha_url = fecha.strftime("%d/%m/%Y")
fecha_csv = fecha.strftime("%Y-%m-%d")

url = (
    "https://www.enagas.es/content/enagas/es/gestion-tecnica-sistema/"
    "energy-data/parametros-fisicos/capacidades-tecnicas-flujos-fisicos/"
    "seguimiento-diario-sistema/jcr:content/responsiveGrid/"
    f"dailysystemtracking.dailysystemtrackingdto.xls?date={fecha_url}"
)

# Descargar excel temporal
r = requests.get(url, timeout=60)
r.raise_for_status()

excel_temp = "temporal.xlsx"

with open(excel_temp, "wb") as f:
    f.write(r.content)

# Leer hoja
df = pd.read_excel(excel_temp, header=None)

# Convertir toda la hoja a lista
valores = df.fillna("").values.tolist()

demanda_nacional = None
convencional = None
sector_electrico = None

for i, fila in enumerate(valores):

    if "Demanda Nacional" in map(str, fila):
        demanda_nacional = float(valores[i+1][1])

    if "Convencional" in map(str, fila):
        convencional = float(valores[i+1][1])

    if "Sector Eléctrico" in map(str, fila):
        sector_electrico = float(valores[i+1][1])

# Crear registro
nuevo = pd.DataFrame([{
    "Fecha": fecha_csv,
    "Demanda Nacional": demanda_nacional,
    "Convencional": convencional,
    "Sector Eléctrico": sector_electrico
}])

csv_file = "historico_demanda.csv"

if os.path.exists(csv_file):
    historico = pd.read_csv(csv_file)

    historico = historico[
        historico["Fecha"] != fecha_csv
    ]

    historico = pd.concat(
        [historico, nuevo],
        ignore_index=True
    )
else:
    historico = nuevo

historico = historico.sort_values("Fecha")

historico.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)

print(historico.tail())
