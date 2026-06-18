from fr24sdk.client import Client
import pandas as pd
import time
import os

API_TOKEN = ""

# CSV donde tienes la columna operated_as
archivo_entrada = "creacion_dataframe.csv"

# CSV de salida
archivo_salida = "aerolineas_fr24.csv"

df = pd.read_csv(archivo_entrada)

# Sacamos los ICAO únicos de aerolíneas
codigos_icao = (
    df["operated_as"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

datos_aerolineas = []

with Client(api_token=API_TOKEN) as client:
    for icao in codigos_icao:
        try:
            airline = client.airlines.get_light(icao=icao)

            datos_aerolineas.append({
                "icao": getattr(airline, "icao", None),
                "iata": getattr(airline, "iata", None),
                "name": getattr(airline, "name", None)
            })

            print(f"OK: {icao}")

            time.sleep(10)

        except Exception as e:
            print(f"Error con {icao}: {e}")

            datos_aerolineas.append({
                "icao": icao,
                "iata": None,
                "name": None
            })

            time.sleep(10)

df_aerolineas = pd.DataFrame(datos_aerolineas)

df_aerolineas.to_csv(archivo_salida, index=False)

print("CSV generado:", archivo_salida)
print(df_aerolineas.head())