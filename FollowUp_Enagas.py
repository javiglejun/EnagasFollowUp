from datetime import date, timedelta
import pandas as pd
import requests
import time

fecha_inicio = date(2025, 1, 1)
fecha_fin = date.today() - timedelta(days=1)

registros = []

fecha_actual = fecha_inicio

while fecha_actual <= fecha_fin:

    try:

        fecha_url = fecha_actual.strftime("%d/%m/%Y")
        fecha_csv = fecha_actual.strftime("%Y-%m-%d")

        print(f"Procesando {fecha_csv}")

        url = (
            "https://www.enagas.es/content/enagas/es/gestion-tecnica-sistema/"
            "energy-data/parametros-fisicos/capacidades-tecnicas-flujos-fisicos/"
            "seguimiento-diario-sistema/jcr:content/responsiveGrid/"
            f"dailysystemtracking.dailysystemtrackingdto.xls?date={fecha_url}"
        )

        r = requests.get(url, timeout=60)

        if r.status_code != 200:
            print(f"No disponible: {fecha_csv}")
            fecha_actual += timedelta(days=1)
            continue

        with open("temp.xls", "wb") as f:
            f.write(r.content)

        df = pd.read_excel("temp.xls", header=None)

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

        if (
            demanda is not None
            and convencional is not None
            and sector is not None
        ):

            registros.append({
                "Fecha": fecha_csv,
                "Demanda Nacional": demanda,
                "Convencional": convencional,
                "Sector Eléctrico": sector
            })

        time.sleep(1)

    except Exception as e:
        print(f"Error en {fecha_actual}: {e}")

    fecha_actual += timedelta(days=1)

historico = pd.DataFrame(registros)

historico.to_csv(
    "historico_demanda.csv",
    index=False,
    encoding="utf-8-sig"
)

print(historico.tail())
print(f"Registros descargados: {len(historico)}")
