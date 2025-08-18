import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import adafruit_dht
import board

# === Konfigurasi ===
BROKER = "broker.hivemq.com"   # broker MQTT gratis
PORT   = 1883
TOPIC  = "haris/relay"         # topik MQTT

PIN    = 17                    # Relay pakai GPIO17 (BCM17) agar tidak bentrok DHT di GPIO2
dhtpin = board.D2              # DHT11 di GPIO2 (matikan I2C agar stabil)

# === Setup GPIO (relay aktif-low) ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)
GPIO.output(PIN, GPIO.HIGH)    # default relay OFF (aktif-low: OFF = HIGH)

# === Setup DHT ===
dht_device = adafruit_dht.DHT11(dhtpin)

# === Callback MQTT ===
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke MQTT broker" if rc == 0 else f"Gagal connect rc={rc}")
    if rc == 0:
        client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    pesan = msg.payload.decode().upper().strip()
    print(f"Pesan diterima: {pesan}")

    if pesan == "ON":
        GPIO.output(PIN, GPIO.LOW)   # aktif-low: LOW = ON
        print("Relay ON")
    elif pesan == "OFF":
        GPIO.output(PIN, GPIO.HIGH)  # aktif-low: HIGH = OFF
        print("Relay OFF")

# === MQTT Client ===
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

# Jalankan loop MQTT di background
client.loop_start()

try:
    while True:
        try:
            temperature = dht_device.temperature
            humidity    = dht_device.humidity
            if temperature is not None:
                client.publish("data/a", str(temperature))
                print("Temp:", temperature)
            # (opsional) publish kelembapan juga:
            # if humidity is not None:
            #     client.publish("data/h", str(humidity))
        except Exception:
            # DHT memang kadang gagal baca, coba lagi nanti
            pass

        time.sleep(2)  # jeda agar stabil & tidak spam broker

except KeyboardInterrupt:
    print("Keluar...")

finally:
    client.loop_stop()
    GPIO.cleanup()
    try:
        dht_device.exit()
    except Exception:
        pass
