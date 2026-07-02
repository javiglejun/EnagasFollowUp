from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import requests

# ==========================================
# FECHA DE AYER
# ==========================================

hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
fecha = hoy - timedelta(days=1)

fecha_url = fecha.strftime("%d/%m/%Y")

url = (
    "https://www.enagas.es/content/enagas/es/gestion-tecnica-sistema/"
    "energy-data/parametros-fisicos/capacidades-tecnicas-flujos-fisicos/"
    "seguimiento-diario-sistema/jcr:content/responsiveGrid/"
    f"dailysystemtracking.dailysystemtrackingdto.xls?date={fecha_url}"
)

print("Descargando:", url)

# ==========================================
# DESCARGA DEL EXCEL
# ==========================================

r = requests.get(url, timeout=60)
r.raise_for_status()

with open("temp.xls", "wb") as f:
    f.write(r.content)

print("Excel descargado correctamente")

# ==========================================
# LECTURA DEL EXCEL
# ==========================================

df = pd.read_excel("temp.xls", header=None)

print("===== INICIO EXCEL =====")
print(df.head(50))
print("===== FIN EXCEL =====")

# ==========================================
# CONVERTIR EN LISTA SIMPLE
# ==========================================

datos = (
    df.fillna("")
      .astype(str)
      .values
      .flatten()
      .tolist()
)

print("TOTAL ELEMENTOS:", len(datos))

# ==========================================
# BUSCAR TEXTOS CLAVE
# ==========================================

for i, valor in enumerate(datos):

    texto = str(valor).strip()

    if "Demanda Nacional" in texto:
        print("\n")
        print("===== DEMANDA NACIONAL =====")
        print(datos[i:i+20])

    if "Convencional" == texto:
        print("\n")
        print("===== CONVENCIONAL =====")
        print(datos[i:i+20])

    if "Sector Eléctrico" in texto:
        print("\n")
        print("===== SECTOR ELECTRICO =====")
        print(datos[i:i+20])

print("FIN DEL SCRIPT")
