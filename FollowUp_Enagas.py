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

print("Descargando:", url)

# Descargar fichero
r = requests.get(url, timeout=60)
r.raise_for_status()

with open("temp.xls", "wb") as f:
    f.write(r.content)

# Leer Excel
df = pd.read_excel("temp.xls", header=None)

# Convertir a lista plana
datos = (
    df.fillna("")
      .astype(str)
      .values
      .flatten()
      .tolist()
)

demanda = None
convencional = None
sector = None

for i, valor in enumerate(datos):

    texto = str(valor).strip()

    if texto == "Demanda Nacional":
        demanda = float(datos[i + 2])

    elif texto == "Convencional":
        convencional = float(datos[i + 2])

    elif texto == "Sector Eléctrico":
        sector = float(datos[i + 2])

print("Demanda Nacional:", demanda)
print("Convencional:", convencional)
print("Sector Eléctrico:", sector)

nuevo_registro = pd.DataFrame([{
    "Fecha": fecha_csv,
    "Demanda Nacional": demanda,
    "Convencional": convencional,
    "Sector Eléctrico": sector
}])

csv_file = "historico_demanda.csv"

if os.path.exists(csv_file):

    historico = pd.read_csv(csv_file)

    historico = historico[
        historico["Fecha"] != fecha_csv
    ]

    historico = pd.concat(
        [historico, nuevo_registro],
        ignore_index=True
    )

else:
    historico = nuevo_registro

historico = historico.sort_values("Fecha")

historico.to_csv(
    csv_file,
    index=False,
    encoding="utf-8-sig"
)

print("CSV actualizado correctamente")
print(historico.tail())
