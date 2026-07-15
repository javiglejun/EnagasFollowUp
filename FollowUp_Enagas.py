from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import os
import time


CSV_FILE = "historico_demanda.csv"

BASE_URL = (
    "https://www.enagas.es/content/enagas/es/gestion-tecnica-sistema/"
    "energy-data/parametros-fisicos/capacidades-tecnicas-flujos-fisicos/"
    "seguimiento-diario-sistema/jcr:content/responsiveGrid/"
    "dailysystemtracking.dailysystemtrackingdto.xls"
)


def obtener_fecha_fin():
    """
    Enagás publica normalmente los datos del día anterior.
    Por eso, la fecha final será ayer en horario de Madrid.
    """

    hoy_madrid = datetime.now(ZoneInfo("Europe/Madrid")).date()
    fecha_fin = hoy_madrid - timedelta(days=1)

    return fecha_fin


def obtener_fecha_inicio():
    """
    Lee el histórico existente y calcula desde qué fecha hay que continuar.
    No reconstruye todo el histórico.
    Solo descarga desde el día siguiente a la última fecha guardada.
    """

    if not os.path.exists(CSV_FILE):
        raise Exception(
            f"No existe el fichero {CSV_FILE}. "
            "Como ya tienes el histórico desde 01/01/2025, asegúrate de que "
            "historico_demanda.csv está subido al repositorio."
        )

    historico = pd.read_csv(CSV_FILE)

    if historico.empty:
        raise Exception(
            f"El fichero {CSV_FILE} existe pero está vacío. "
            "Debes subir primero el histórico ya generado."
        )

    if "Fecha" not in historico.columns:
        raise Exception(
            f"El fichero {CSV_FILE} no contiene una columna llamada 'Fecha'."
        )

    historico["Fecha"] = pd.to_datetime(historico["Fecha"], errors="coerce")

    if historico["Fecha"].isna().all():
        raise Exception(
            "No se han podido interpretar las fechas del histórico."
        )

    ultima_fecha = historico["Fecha"].max().date()
    fecha_inicio = ultima_fecha + timedelta(days=1)

    print(f"Última fecha existente en el histórico: {ultima_fecha}")
    print(f"Primera fecha nueva a descargar: {fecha_inicio}")

    return fecha_inicio


def construir_url(fecha_objetivo):
    """
    Construye la URL de descarga del Excel de Enagás.
    La fecha va en formato dd/mm/yyyy.
    """

    fecha_url = fecha_objetivo.strftime("%d/%m/%Y")
    url = f"{BASE_URL}?date={fecha_url}"

    return url


def buscar_siguiente_numero(datos, posicion_inicio):
    """
    Busca el primer valor numérico después de una etiqueta.

    En el Excel de Enagás, por ejemplo:
    Demanda Nacional, '', 800.339...

    Por eso no conviene asumir siempre i+1 o i+2.
    Esta función busca el primer número después del texto.
    """

    valores_posteriores = datos[posicion_inicio + 1:posicion_inicio + 15]

    for valor in valores_posteriores:
        texto = str(valor).strip()

        if texto == "":
            continue

        try:
            return float(texto)
        except ValueError:
            continue

    return None


def descargar_y_extraer(fecha_objetivo):
    """
    Descarga el Excel de Enagás para una fecha concreta y extrae:
    - Demanda Nacional
    - Convencional
    - Sector Eléctrico
    """

    fecha_csv = fecha_objetivo.strftime("%Y-%m-%d")
    url = construir_url(fecha_objetivo)

    print("")
    print(f"Procesando fecha: {fecha_csv}")
    print(f"URL: {url}")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    if len(response.content) < 5000:
        raise ValueError(
            f"El fichero descargado para {fecha_csv} parece demasiado pequeño."
        )

    with open("temp.xls", "wb") as f:
        f.write(response.content)

    df = pd.read_excel("temp.xls", header=None)
    print("\n===================================")
    print("DATAFRAME COMPLETO")
    print("===================================")

    with pd.option_context(
        'display.max_rows', None,
        'display.max_columns', None,
        'display.width', 1000
    ):
    print(df)

    datos = (
        df.fillna("")
          .astype(str)
          .values
          .flatten()
          .tolist()
    )

    demanda_nacional = None
    convencional = None
    sector_electrico = None

    for i, valor in enumerate(datos):
        texto = str(valor).strip()

        if texto == "Demanda Nacional":
            demanda_nacional = buscar_siguiente_numero(datos, i)

        elif texto == "Convencional":
            convencional = buscar_siguiente_numero(datos, i)

        elif texto == "Sector Eléctrico":
            sector_electrico = buscar_siguiente_numero(datos, i)

    if demanda_nacional is None:
        raise ValueError(f"No se ha encontrado Demanda Nacional para {fecha_csv}")

    if convencional is None:
        raise ValueError(f"No se ha encontrado Convencional para {fecha_csv}")

    if sector_electrico is None:
        raise ValueError(f"No se ha encontrado Sector Eléctrico para {fecha_csv}")

    registro = {
        "Fecha": fecha_csv,
        "Demanda Nacional": demanda_nacional,
        "Convencional": convencional,
        "Sector Eléctrico": sector_electrico
    }

    print("Registro extraído correctamente:")
    print(registro)

    return registro


def cargar_historico_existente():
    """
    Carga el histórico existente.
    """

    historico = pd.read_csv(CSV_FILE)

    return historico


def guardar_historico(historico):
    """
    Limpia duplicados, ordena por fecha y guarda el CSV.
    """

    historico["Fecha"] = pd.to_datetime(historico["Fecha"], errors="coerce")
    historico = historico.dropna(subset=["Fecha"])

    historico["Fecha"] = historico["Fecha"].dt.strftime("%Y-%m-%d")

    historico = historico.drop_duplicates(
        subset=["Fecha"],
        keep="last"
    )

    historico = historico.sort_values("Fecha")

    historico.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("")
    print("Histórico guardado correctamente.")
    print("Últimas filas del histórico:")
    print(historico.tail())
    print(f"Total registros en histórico: {len(historico)}")


def main():
    print("Inicio del proceso de actualización de Enagás")

    fecha_inicio = obtener_fecha_inicio()
    fecha_fin = obtener_fecha_fin()

    print(f"Fecha inicio: {fecha_inicio}")
    print(f"Fecha fin: {fecha_fin}")

    if fecha_inicio > fecha_fin:
        print("El histórico ya está actualizado. No hay nuevas fechas que descargar.")
        return

    historico = cargar_historico_existente()
    nuevos_registros = []

    fecha_actual = fecha_inicio

    while fecha_actual <= fecha_fin:
        try:
            registro = descargar_y_extraer(fecha_actual)
            nuevos_registros.append(registro)

        except Exception as e:
            print(f"Error procesando {fecha_actual}: {e}")

        fecha_actual += timedelta(days=1)

        # Pausa breve para no hacer demasiadas peticiones seguidas
        time.sleep(1)

    if nuevos_registros:
        nuevos_df = pd.DataFrame(nuevos_registros)

        historico_actualizado = pd.concat(
            [historico, nuevos_df],
            ignore_index=True
        )

        guardar_historico(historico_actualizado)

    else:
        print("No se ha añadido ningún registro nuevo.")


if __name__ == "__main__":
    main()
