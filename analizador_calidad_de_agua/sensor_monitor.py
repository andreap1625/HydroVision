import time
import threading
import datetime
from w1thermsensor import W1ThermSensor

import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS

SAVE_FILE = "last_measurement.txt"
TDS_CHANNEL = 0  # ADS1115 A0
PH_CHANNEL = 1   # ADS1115 A1
VOLTAGE_REF = 5.0  
GAIN = 1  

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = GAIN

chan_tds = AnalogIn(ads, ADS.P0)
chan_ph = AnalogIn(ads, ADS.P1)

sensor = W1ThermSensor()
should_save = False
last_measurement = None

def wait_for_enter():
    global should_save
    while True:
        input()
        should_save = True

threading.Thread(target=wait_for_enter, daemon=True).start()

print("Live ADS1115 Sensor Monitor")
print("Press ENTER to save the current reading.\n")

try:
    while True:
        try:
            # Read voltage
            tds_v = chan_tds.voltage
            ph_v = chan_ph.voltage
            temp_c = sensor.get_temperature()

            # Convert
            ph = 7 + ((ph_v - 2.5) / 0.18)
            tds = (133.42 * tds_v**3 - 255.86 * tds_v**2 + 857.39 * tds_v) * 0.5

            last_measurement = {
                'tds': round(tds, 2),
                'ph': round(ph, 2),
                'temp': round(temp_c, 2)
            }

            print(f"\rTDS: {last_measurement['tds']} ppm | pH: {last_measurement['ph']} | Temp: {last_measurement['temp']} °C", end='')

            if should_save:
                should_save = False
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(SAVE_FILE, "w") as f:
                    f.write(f"{now},TDS={last_measurement['tds']} ppm,PH={last_measurement['ph']},Temp={last_measurement['temp']} C\n")
                print(f"\nSaved to '{SAVE_FILE}' at {now}")

        except Exception as e:
            print(f"\nError: {e}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping.")

