import time
import alarm
import digitalio
import neopixel
import ssl
import busio
import board
import wifi
import socketpool
import adafruit_sht4x
import adafruit_requests
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

def sleep():
    np_power = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
    np_power.switch_to_output(value=False)

    np = neopixel.NeoPixel(board.NEOPIXEL, 1)

    np[0] = (50, 50, 50)
    time.sleep(1)
    np[0] = (0, 0, 0)
    
    sleepSeconds = 900
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleepSeconds)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)

def convertTemp(c):
    return (c * 9/5) + 32

def connectWifi():
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print("My IP address is", wifi.radio.ipv4_address)

def sendMetrics(metrics):
    aio_username = secrets["aio_username"]
    aio_key = secrets["aio_key"]
    
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())

    # Initialize an Adafruit IO HTTP API object
    io = IO_HTTP(aio_username, aio_key, requests)

    try:
        # Get the 'temperature' feed from Adafruit IO
        temperature_feed = io.get_feed("temperature")
    except AdafruitIO_RequestError:
        # If no 'temperature' feed exists, create one
        temperature_feed = io.create_new_feed("temperature")

    # Send random integer values to the feed
    temperature = convertTemp(metrics[0])
    print("Sending {0} to temperature feed...".format(temperature))
    io.send_data(temperature_feed["key"], temperature)
    print("Data sent!")


sht = adafruit_sht4x.SHT4x(busio.I2C(board.SCL1, board.SDA1))
sht.mode = adafruit_sht4x.Mode.NOHEAT_LOWPRECISION

temperature, relative_humidity = sht.measurements

print("Temperature: %0.1f F" % convertTemp(temperature))
print("Humidity: %0.1f %%" % relative_humidity)
time.sleep(1)
connectWifi()
sendMetrics(sht.measurements)
sleep()