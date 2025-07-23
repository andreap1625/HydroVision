import os
import csv
from datetime import datetime
import pandas as pd

# Obtener la ruta absoluta del directorio donde está este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DATA = os.path.join(BASE_DIR, 'data')
RUTA_GUARDAR = os.path.join(RUTA_DATA, 'new_data')

# Cargar dataset original
reference_path = os.path.join(RUTA_DATA, 'Datos_ACP_2015_2022.csv')
reference = pd.read_csv(reference_path)
means_calc = reference.mean(numeric_only=True)


# Columnas del CSV final
columns = [
    "ID_estacion", "Fecha", "pH", "Temp", "TDS", "Alc_total", "Ca", "Cl", "Cond",
    "Dureza", "K", "Mg", "Na", "CHL_A", "C_totales", "NNO3", "OD", "ODPCT", "Transp", "Turb"
]

# Leer el .txt
txt_path = os.path.join(RUTA_GUARDAR, "last_measurement.txt")

with open(txt_path, "r") as f:
    lines = f.readlines()

# Preparar datos para CSV
csv_rows = []

for line in lines:
    data = dict.fromkeys(columns, None)

    # ID de estación (temporal)
    data["ID_estacion"] = "TAG"

    # Separar campos
    splits = line.strip().split(",")

    try:
        # Fecha
        f_original = splits[0].strip()
        data['Fecha'] = datetime.strptime(f_original, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")

        # Extraer datos
        for split in splits[1:]:
            if "TDS=" in split:
                data["TDS"] = float(split.split("=")[1].split()[0])
            elif "PH=" in split:
                data["pH"] = float(split.split("=")[1])
            elif "Temp=" in split:
                data["Temp"] = float(split.split("=")[1].split()[0])

            # Calcular Conductividad (Cond) si TDS está presente
        if data["TDS"] is not None:
            data["Cond"] = round(data["TDS"] * 2, 3)
    except Exception as e:
        print(f"Error procesando línea: {line.strip()}\n{e}")
        continue

    # Imputar valores faltantes con media
    for col in columns:
        if data[col] is None:
            data[col] = round(means_calc.get(col, 0), 3)

    csv_rows.append(data)

# Crear carpeta si no existe
os.makedirs(RUTA_GUARDAR, exist_ok=True)

# Escribir el archivo CSV
output_path = os.path.join(RUTA_GUARDAR, "new_measurement.csv")
with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"Archivo CSV guardado exitosamente en: {output_path}")

#Anexar fila a datos de entrenamiento
# Leer la fila del nuevo CSV
new_data_path = os.path.join(RUTA_GUARDAR, "new_measurement.csv")
new_data = pd.read_csv(new_data_path)

# Obtener el año de la fecha en la nueva fila
fecha_str = new_data.loc[0, "Fecha"]  
a = datetime.strptime(fecha_str, "%d/%m/%Y").year

# Nombre del archivo destino
output_filename = f"datos_TAG_{a}.csv"
output_filepath = os.path.join(RUTA_TRAIN, output_filename)

# Crear carpeta si no existe
os.makedirs(RUTA_TRAIN, exist_ok=True)

# Si el archivo no existe, crearlo con encabezado
if not os.path.exists(output_filepath):
    new_data.to_csv(output_filepath, index=False)
    print(f"Archivo creado: {output_filepath}")
else:
    # Si el archivo existe, anexar la fila sin encabezado
    new_data.to_csv(output_filepath, mode='a', header=False, index=False)
    print(f"Fila anexada a: {output_filepath}")
