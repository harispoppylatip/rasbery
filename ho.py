import time
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import adafruit_dht
import board

# === Konfigurasi ===
BROKER = "localhost"           # pakai broker lokal
PORT   = 1883
TOPIC_CMD   = "haris/relay"    # terima perintah ON / OFF
TOPIC_TEMP  = "data/a"         # publish suhu
TOPIC_HUM   = "data/h"         # publish kelembapan

PIN_RELAY   = 17               # Relay di GPIO17 (pin fisik 11)
DHT_PIN     = board.D2         # DHT11 di GPIO2 (pin fisik 3, matikan I2C)
RELAY_ACTIVE_LOW = True

# === Setup GPIO Relay ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_RELAY, GPIO.OUT)
GPIO.output(PIN_RELAY, GPIO.HIGH if RELAY_ACTIVE_LOW else GPIO.LOW)  # default OFF

# === Setup DHT ===
dht_device = adafruit_dht.DHT11(DHT_PIN)

# === Helper Relay ===
def relay_on():
    if RELAY_ACTIVE_LOW:
        GPIO.output(PIN_RELAY, GPIO.LOW)
    else:
        GPIO.output(PIN_RELAY, GPIO.HIGH)

def relay_off():
    if RELAY_ACTIVE_LOW:
        GPIO.output(PIN_RELAY, GPIO.HIGH)
    else:
        GPIO.output(PIN_RELAY, GPIO.LOW)

# === Callback MQTT ===
def on_connect(client, userdata, flags, rc):
    print("✅ Terhubung ke MQTT broker" if rc == 0 else f"❌ Gagal connect rc={rc}")
    if rc == 0:
        client.subscribe(TOPIC_CMD)

def on_message(client, userdata, msg):
    pesan = msg.payload.decode().upper().strip()
    print(f"📩 Pesan diterima: {pesan}")

    if pesan == "ON":
        relay_on()
        print("🔌 Relay ON")
    elif pesan == "OFF":
        relay_off()
        print("🔌 Relay OFF")

# === MQTT Client ===
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    while True:
        try:
            temperature = dht_device.temperature
            humidity    = dht_device.humidity

            if temperature is not None:
                client.publish(TOPIC_TEMP, str(temperature))
                print("🌡️ Suhu:", temperature)

            if humidity is not None:
                client.publish(TOPIC_HUM, str(humidity))
                print("💧 Kelembapan:", humidity)

        except Exception:
            # DHT kadang gagal baca
            pass

        time.sleep(2)

except KeyboardInterrupt:
    print("Keluar...")

finally:
    client.loop_stop()
    GPIO.cleanup()
    try:
        dht_device.exit()
    except Exception:
        pass
