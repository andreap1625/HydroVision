import pandas as pd
import requests
import os

# --- CONFIGURACIÓN ---
UBIDOTS_TOKEN = "BBUS-c9DYYpBbAt3iU8yPeDqUtw8X8dME6s"
DEVICE_LABEL = "hydro_vision_server"
MEASURED_DATA_PATH = os.path.join("data", "new_data", "new_measurement.csv")
PREDICTED_DATA_PATH = "results/predicciones.csv"

HEADERS = {
    "X-Auth-Token": UBIDOTS_TOKEN,
    "Content-Type": "application/json"
}

# --- Verificar archivos ---
if not os.path.exists(MEASURED_DATA_PATH):
    print(f"No se encontró el archivo de datos medidos: {MEASURED_DATA_PATH}")
    exit(1)

if not os.path.exists(PREDICTED_DATA_PATH):
    print(f"No se encontró el archivo de predicciones: {PREDICTED_DATA_PATH}")
    exit(1)

# --- Cargar datos ---
df_measured = pd.read_csv(MEASURED_DATA_PATH, parse_dates=["Fecha"])
df_predicted = pd.read_csv(PREDICTED_DATA_PATH, parse_dates=["Fecha"])

# --- Unir por índice temporal ---
df = pd.merge(df_measured, df_predicted, left_on="Fecha", right_on="Fecha", how="inner")

if df.empty:
    print("No hay datos para enviar (la unión está vacía).")
    exit(1)

# --- Envío a Ubidots ---
def send_value(variable_label, value, timestamp):
    url = f"https://stem.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}/"
    payload = {
        variable_label: float(value),
    }
    response = requests.post(url, headers=HEADERS, json=payload, params={"force": "true"})
    if response.status_code == 200:
        print(f"Enviado: {variable_label} = {value}")
    else:
        print(f"Error al enviar {variable_label}: {response.status_code} - {response.text}")

# --- Iterar sobre todas las filas ---
for _, row in df.iterrows():
    ts = pd.to_datetime(row['Fecha']).timestamp() * 1000

    for var in ["Cond", "Temp", "pH"]:
        # Datos medidos
        if var in row:
            send_value(f"{var.lower()}_measured", row[var], ts)
        # Datos predichos
        pred_col = f"pred_{var}"
        if pred_col in row:
            send_value(f"{var.lower()}_predicted", row[pred_col], ts)
