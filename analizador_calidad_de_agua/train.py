
# ## Training completo


import os
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout


# --- Configuración ---
SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

RUTA_MODELOS = "C:/Users/andre/TopicosEspeciales2/proyecto_final_redes/analizador_calidad_de_agua/models/"
os.makedirs(RUTA_MODELOS, exist_ok=True)


def modelo_lstm_cond(input_shape):
    model = Sequential()
    model.add(LSTM(512, activation='relu', return_sequences=True, input_shape=(1, 17)))
    model.add(LSTM(45, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(35, activation='tanh'))
    model.add(Dropout(0.1))
    model.add(Dense(31, activation='relu'))
    model.add(Dense(1))
    model.compile(optimizer='RMSprop', loss='mse')
    return model

def modelo_lstm_temp(input_shape):
    model = Sequential()
    model.add(LSTM(512, activation='relu', return_sequences=True, input_shape=(1, 17)))
    model.add(LSTM(40, activation='sigmoid'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(45, activation='tanh'))
    model.add(Dense(27, activation='tanh'))
    model.add(Dense(1))
    model.compile(optimizer='Nadam', loss='mae')
    return model

def modelo_lstm_ph(input_shape):
    model = Sequential()
    model.add(LSTM(512, activation='relu', return_sequences=True, input_shape=(1, 17)))
    model.add(LSTM(40, activation='sigmoid'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(45, activation='tanh'))
    model.add(Dense(27, activation='tanh'))
    model.add(Dense(1))
    model.compile(optimizer='Nadam', loss='mae')
    return model


# --- Procesamiento---
def crear_secuencias(data, n_steps):
    X, y = [], []
    for i in range(len(data) - n_steps):
        X.append(data[i:i + n_steps, :-1])
        y.append(data[i + n_steps, -1])
    return np.array(X), np.array(y)


# --- Entrenamiento ---
def entrenar_variable(df, variable, tag):
    print(f"\nEntrenando modelo para {variable}...")

    if variable not in df.columns:
        print(f"Variable {variable} no encontrada en el DataFrame.")
        return

    n_steps = 1
    features = df.select_dtypes(include=[np.number]).columns.tolist()
    if variable in features:
        features.remove(variable)
    data = df[features + [variable]].dropna().values

    # Escalado
    scaler_X = MinMaxScaler()
    scaler_Y = MinMaxScaler()

    X_scaled = scaler_X.fit_transform(data[:, :-1])
    y_scaled = scaler_Y.fit_transform(data[:, -1].reshape(-1, 1))
    data_scaled = np.hstack([X_scaled, y_scaled])

    X, y = crear_secuencias(data_scaled, n_steps)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)

    # Selección de modelo
    input_shape = (X_train.shape[1], X_train.shape[2])
    if variable == 'Cond':
        model = modelo_lstm_cond(input_shape)
        batch_size = 5
        epochs = 35
    elif variable == 'Temp':
        model = modelo_lstm_temp(input_shape)
        batch_size = 5
        epochs = 35
    elif variable == 'pH':
        model = modelo_lstm_ph(input_shape)
        batch_size = 32
        epochs = 35
    else:
        print(f"No hay modelo definido para {variable}")
        return

    # Entrenamiento (sin EarlyStopping)
    model.fit(X_train, y_train, validation_data=(X_test, y_test),
              epochs=epochs, batch_size=batch_size, verbose=1)

    # Guardado
    model.save(os.path.join(RUTA_MODELOS, f"modelo_{tag}_{variable}.h5"))
    joblib.dump(scaler_X, os.path.join(RUTA_MODELOS, f"scaler_X_{tag}_{variable}.pkl"))
    joblib.dump(scaler_Y, os.path.join(RUTA_MODELOS, f"scaler_Y_{tag}_{variable}.pkl"))
    print(f"Modelo y scalers guardados para {variable}.")


# --- Entrenamiento general ---
def entrenar_modelos(datos_TAG, tag="TAG"):
    for variable in ["Cond", "Temp", "pH"]:
        entrenar_variable(datos_TAG.copy(), variable, tag)


# Cargar datos
df = pd.read_csv('datos_TAG.csv', parse_dates=["Fecha"])
#df = df.dropna()
df = df.sort_values("Fecha")
df.set_index("Fecha", inplace=True)
print(df.head())


numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns

for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

print("Outliers eliminados usando IQR en columnas numéricas.")
print(df.head())


# Verificar índice correcto
assert pd.api.types.is_datetime64_any_dtype(df.index), "El índice no es datetime"


entrenar_modelos(df, tag="tag")

if __name__ == "__main__":

    print(f"\nReentrenando modelo...")
    entrenar_modelos(df, tag="tag")

    print("\nReentrenamiento completado y modelos guardados.")


