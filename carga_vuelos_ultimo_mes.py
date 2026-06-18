from datetime import datetime, timedelta, timezone
from fr24sdk.client import Client
from fr24sdk.exceptions import RateLimitError
import pandas as pd
import time
import os


API_TOKEN = ""


AEROPUERTOS_ESPANA = [
    "LEBL",  # Barcelona
    "LEBB",  # Bilbao
    "LEIB",  # Ibiza
    "GCLA",  # La Palma
    "LEMD",  # Madrid
    "LEPA",  # Palma de Mallorca
    "LEZL",  # Sevilla
    "LEVC"   # Valencia
]


fecha_inicio = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
fecha_fin = datetime(2026, 6, 18, 0, 0, 0, tzinfo=timezone.utc)


carpeta_salida = "datos_fr24_2026"
os.makedirs(carpeta_salida, exist_ok=True)


ESPERA_NORMAL = 10
ESPERA_ERROR = 10
ESPERA_RATE_LIMIT = 90
MAX_INTENTOS = 3

with Client(api_token=API_TOKEN) as client:
    fecha_actual = fecha_inicio

    while fecha_actual < fecha_fin:
        fecha_siguiente = fecha_actual + timedelta(days=1)

        nombre_csv = f"{carpeta_salida}/vuelos_espana_{fecha_actual.date()}.csv"

        if os.path.exists(nombre_csv):
            print(f"Ya existe {nombre_csv}, se salta este día.")
            fecha_actual = fecha_siguiente
            continue

        print(f"Procesando día {fecha_actual.date()}")

        datos_dia = []

        for aeropuerto in AEROPUERTOS_ESPANA:
            intentos = 0
            completado = False

            while intentos < MAX_INTENTOS and not completado:
                try:
                    response = client.flight_summary.get_light(
                        flight_datetime_from=fecha_actual,
                        flight_datetime_to=fecha_siguiente,
                        airports=[f"both:{aeropuerto}"],
                        limit=20000
                    )

                    for vuelo in response.data:
                        datos_dia.append({
                            "fr24_id": vuelo.fr24_id,
                            "flight": vuelo.flight,
                            "callsign": vuelo.callsign,
                            "operated_as": vuelo.operating_as,
                            "type": vuelo.type,
                            "reg": vuelo.reg,
                            "origin_icao": vuelo.orig_icao,
                            "destination_icao": vuelo.dest_icao,
                            "datetime_takeoff": vuelo.datetime_takeoff,
                            "datetime_landed": vuelo.datetime_landed
                        })

                    completado = True
                    time.sleep(ESPERA_NORMAL)

                except RateLimitError:
                    intentos += 1

                    print(
                        f"Rate limit con {aeropuerto} en {fecha_actual.date()}. "
                        f"Intento {intentos}/{MAX_INTENTOS}. "
                        f"Esperando {ESPERA_RATE_LIMIT} segundos..."
                    )

                    time.sleep(ESPERA_RATE_LIMIT)

                except Exception as e:
                    print(f"Error con {aeropuerto} en {fecha_actual.date()}: {e}")

                    completado = True
                    time.sleep(ESPERA_ERROR)

            if not completado:
                print(
                    f"No se pudo consultar {aeropuerto} en {fecha_actual.date()} "
                    f"después de {MAX_INTENTOS} intentos."
                )

        df_dia = pd.DataFrame(datos_dia)

        if not df_dia.empty:
            print(f"Registros antes de quitar duplicados: {len(df_dia)}")

            if "fr24_id" in df_dia.columns:
                df_dia = df_dia.drop_duplicates(subset=["fr24_id"])

            print(f"Registros después de quitar duplicados: {len(df_dia)}")

            df_dia.to_csv(nombre_csv, index=False)

            print(f"Guardado CSV: {nombre_csv}")
        else:
            print(f"No hay datos para {fecha_actual.date()}")

        fecha_actual = fecha_siguiente