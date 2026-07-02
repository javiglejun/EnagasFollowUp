import pandas as pd
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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

# Descargar fichero
r = requests.get(url, timeout=60)
r.raise_for_status()

with open("temp.xls", "wb") as f:
    f.write(r.content)

# Leer excel
df = pd.read_excel("temp.xls", header=None)

print("===== INICIO EXCEL =====")
print(df.head(40))
print("===== FIN EXCEL =====")

# Convertir toda la hoja en una lista simple
datos = df.astype(str).fillna("").stack().tolist()

demanda = None
convencional = None
sector = None

for i, valor in enumerate(datos):

    if valor == "Demanda Nacional":
        demanda = float(datos[i + 1])

    elif valor == "Convencional":
        convencional = float(datos[i + 1])

    elif valor == "Sector Eléctrico":
        sector = float(datos[i + 1])

registro = pd.DataFrame([{
    "Fecha": fecha_csv,
    "Demanda Nacional": demanda,
    "Convencional": convencional,
    "Sector Eléctrico": sector
}])

csv_file = "historico_demanda.csv"

if os.path.exists(csv_file):
    historico = pd.read_csv(csv_file)
    historico = historico[historico["Fecha"] != fecha_csv]
    historico = pd.concat([historico, registro], ignore_index=True)
else:
    historico = registro

historico.to_csv(csv_file, index=False)

print(historico.tail())
