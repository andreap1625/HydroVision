import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import sys

RUTA_VIGILADA = "data/new_data/"
RUTA_RESULTADOS = "results/"
ARCHIVO_TXT = os.path.join(RUTA_VIGILADA, "last_measurement.txt")
ARCHIVO_CSV = os.path.join(RUTA_VIGILADA, "new_measurement.csv")
ARCHIVO_PREDICCION = os.path.join(RUTA_RESULTADOS, "predicciones.csv")

class EventoNuevoArchivo(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith(".txt"):
            nombre_archivo = os.path.basename(event.src_path)
            print(f"\nNuevo archivo .txt detectado: {nombre_archivo}")
            time.sleep(1)

            print("Ejecutando script de conversión: change_format.py")
            subprocess.run([sys.executable, "change_format.py"], check=True)

            print("Esperando a que se genere el archivo .csv...")
            timeout = 10
            espera = 0
            while not os.path.exists(ARCHIVO_CSV) and espera < timeout:
                time.sleep(1)
                espera += 1

            if not os.path.exists(ARCHIVO_CSV):
                print("Error: No se generó el archivo .csv esperado.")
                return
            else:
                print("Archivo correctamente guardado")

            print("Ejecutando predicción...")

            proceso = subprocess.Popen(
                [sys.executable, "prediction.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            while True:
                salida = proceso.stdout.readline()
                if salida == '' and proceso.poll() is not None:
                    break
                if salida:
                    print(f"[PREDICCIÓN] {salida.strip()}")

            codigo_salida = proceso.poll()
            print(f"Predicción finalizada con código: {codigo_salida}")

            if codigo_salida == 0 and os.path.exists(ARCHIVO_PREDICCION):
                print("Enviando datos a Ubidots...")

                try:
                    subprocess.run([sys.executable, "ubiSend.py", ARCHIVO_PREDICCION], check=True)
                    print("Datos enviados a Ubidots correctamente.")
                except subprocess.CalledProcessError as e:
                    print(f"Error al enviar a Ubidots: {e}")
            else:
                print("Predicción fallida o archivo de predicción no encontrado.")

            print("Flujo completo finalizado para:", nombre_archivo)

if __name__ == "__main__":
    print(f"Vigilando carpeta: {RUTA_VIGILADA}")
    event_handler = EventoNuevoArchivo()
    observer = Observer()
    observer.schedule(event_handler, path=RUTA_VIGILADA, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
