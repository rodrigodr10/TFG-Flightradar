from fr24sdk.client import Client
from fr24sdk.exceptions import RateLimitError
import pandas as pd
import time


API_TOKEN = ""

archivo_entrada = "icao_aeropuertos.csv"
archivo_salida = "aeropuertos_fr24.csv"

ESPERA_NORMAL = 10
ESPERA_RATE_LIMIT = 60
MAX_INTENTOS = 3


def obtener_atributo(objeto, *nombres):
    for nombre in nombres:
        if hasattr(objeto, nombre):
            return getattr(objeto, nombre)
    return None


df = pd.read_csv(archivo_entrada)

codigos_icao = (
    df["icao"]
    .dropna()
    .astype(str)
    .str.strip()
    .str.upper()
    .unique()
)

datos_aeropuertos = []

with Client(api_token=API_TOKEN) as client:
    for codigo_icao in codigos_icao:
        intentos = 0
        completado = False

        while intentos < MAX_INTENTOS and not completado:
            try:
                respuesta = client.airports.get_light(code=codigo_icao)

                if hasattr(respuesta, "data"):
                    airport = respuesta.data
                else:
                    airport = respuesta

                datos_aeropuertos.append({
                    "icao": obtener_atributo(airport, "icao") or codigo_icao,
                    "iata": obtener_atributo(airport, "iata"),
                    "name": obtener_atributo(airport, "name")
                })

                print(f"OK: {codigo_icao}")
                completado = True
                time.sleep(ESPERA_NORMAL)

            except RateLimitError:
                intentos += 1

                print(
                    f"Rate limit con {codigo_icao}. "
                    f"Intento {intentos}/{MAX_INTENTOS}. "
                    f"Esperando {ESPERA_RATE_LIMIT} segundos..."
                )

                time.sleep(ESPERA_RATE_LIMIT)

            except Exception as e:
                print(f"Error con {codigo_icao}: {e}")

                datos_aeropuertos.append({
                    "icao": codigo_icao,
                    "iata": None,
                    "name": None
                })

                completado = True
                time.sleep(ESPERA_NORMAL)

        if not completado:
            datos_aeropuertos.append({
                "icao": codigo_icao,
                "iata": None,
                "name": None
            })

df_aeropuertos = pd.DataFrame(datos_aeropuertos)

df_aeropuertos.to_csv(archivo_salida, index=False)

print(f"CSV generado: {archivo_salida}")
print(df_aeropuertos.head())