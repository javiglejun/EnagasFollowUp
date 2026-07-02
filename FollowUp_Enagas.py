from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import os

# Fecha de ayer
hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
fecha = hoy - timedelta(days=1)

fecha_url = fecha.strftime("%d/%m/%Y")
fecha_nombre = fecha.strftime("%Y%m%d")

url = (
    "https://www.enagas.es/content/enagas/es/gestion-tecnica-sistema/"
    "energy-data/parametros-fisicos/capacidades-tecnicas-flujos-fisicos/"
    "seguimiento-diario-sistema/jcr:content/responsiveGrid/"
    f"dailysystemtracking.dailysystemtrackingdto.xls?date={fecha_url}"
)

os.makedirs("data", exist_ok=True)

nombre_fichero = f"data/ParPreDia{fecha_nombre}.xls"

r = requests.get(url, timeout=60)

if r.status_code == 200:
    with open(nombre_fichero, "wb") as f:
        f.write(r.content)
    print(f"Descargado: {nombre_fichero}")
else:
    raise Exception(f"Error {r.status_code}")
