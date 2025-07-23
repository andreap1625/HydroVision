import os
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler

# --- Configuración ---
SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)


DATA_PATH = os.path.join("data", "new_data", "new_measurement.csv")
MODEL_DIR = "models/"
OUTPUT_DIR = "results/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VARIABLES = ["Cond", "Temp", "pH"]
TAG = "tag"  

# --- Cargar datos ---
df = pd.read_csv(DATA_PATH, parse_dates=["Fecha"])
df = df.sort_values("Fecha")
df.set_index("Fecha", inplace=True)

# --- Procesamiento de outliers igual al entrenamiento ---
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

# --- Predicción ---
resultados = pd.DataFrame(index=df.index)

for var in VARIABLES:
    print(f"\nProcesando predicción para: {var}")

    model_path = os.path.join(MODEL_DIR, f"modelo_{TAG}_{var}.h5")
    scaler_X_path = os.path.join(MODEL_DIR, f"scaler_X_{TAG}_{var}.pkl")
    scaler_Y_path = os.path.join(MODEL_DIR, f"scaler_Y_{TAG}_{var}.pkl")

    if not os.path.exists(model_path):
        print(f"Modelo para {var} no encontrado. Saltando...")
        continue

    # Cargar modelo y escaladores
    model = tf.keras.models.load_model(model_path, compile=False)
    scaler_X = joblib.load(scaler_X_path)
    scaler_Y = joblib.load(scaler_Y_path)

    # Seleccionar y escalar datos
    features = df.select_dtypes(include=[np.number]).columns.tolist()
    if var in features:
        features.remove(var)

    df_input = df[features].dropna()
    X_input = scaler_X.transform(df_input.values)

    # Redimensionar para LSTM (1 timestep)
    X_input = X_input.reshape((X_input.shape[0], 1, X_input.shape[1]))

    y_pred_scaled = model.predict(X_input)
    y_pred = scaler_Y.inverse_transform(y_pred_scaled)

    # Alinear resultados
    pred_df = pd.DataFrame(y_pred, index=df_input.index, columns=[f"pred_{var}"])
    resultados = resultados.join(pred_df, how="outer")

# --- Guardar resultados ---
resultados.to_csv(os.path.join(OUTPUT_DIR, "predicciones.csv"))
print(f"\nPredicciones guardadas en {OUTPUT_DIR}/predicciones.csv")
