from machine import Pin, PWM
from microdot import Microdot, Response
import network
import time

state_file = "state.txt"
index_file = "index.html"

max_luma = 100
max_duty = 65535
max_rgb = 255

current_rgb = []

red_pin = Pin(0, mode=Pin.OUT)
green_pin = Pin(1, mode=Pin.OUT)
blue_pin = Pin(2, mode=Pin.OUT)

red_pwm = PWM(red_pin, freq=120)
green_pwm = PWM(green_pin, freq=120)
blue_pwm = PWM(blue_pin, freq=120)

app = Microdot()


# Web routes
@app.post("/color")
def set_color(request):
    body = get_body(request)
    if not body:
        return Response(status_code=400)

    values = body.split(",")
    values = list(map(float, values))

    set_led(values)
    return Response(status_code=200)


@app.get("/color")
def get_color(request):
    return ",".join(map(str, current_rgb))


@app.post("/brightness")
def set_brightness(request):
    body = get_body(request)

    new_luma = float(body)
    old_luma = calc_luma(current_rgb)

    r = new_luma / old_luma
    if r > 1:
        r_max = max_rgb / max(current_rgb)
        r = min(r, r_max)

    new_rgb = list(map(lambda x: r * x, current_rgb))
    set_led(new_rgb)
    return Response(status_code=200)


@app.get("/brightness")
def get_brightness(request):
    luma = calc_luma(current_rgb)
    return str(luma)


@app.get("/")
def get_index(request):
    try:
        with open(index_file) as file:
            content = file.read()
            return Response(content, headers={"Content-Type": "text/html"})
    except OSError:
        return Response("Index file not found", status_code=404)


# Helper functions
def get_body(request):
    return str(request.body, "utf-8")


def map_rgb_to_duty(rgb):
    return max(round(rgb / max_rgb * max_duty), 0)


def set_led(values):
    red_pwm.duty_u16(map_rgb_to_duty(values[0]))
    green_pwm.duty_u16(map_rgb_to_duty(values[1]))
    blue_pwm.duty_u16(map_rgb_to_duty(values[2]))
    save_rgb(values)


def calc_luma(values):
    R = values[0] / max_rgb
    G = values[1] / max_rgb
    B = values[2] / max_rgb
    Y = 0.3 * R + 0.59 * G + 0.11 * B
    return max_luma * Y


def load_rgb():
    try:
        with open(state_file) as file:
            state = file.read()
            if state:
                rgb_vals = state.split(",")
                set_led(list(map(float, rgb_vals)))
    except:
        set_led([255, 0, 0])


def save_rgb(values):
    global current_rgb
    current_rgb = values

    with open(state_file, "w") as file:
        state = ",".join(map(str, values))
        file.write(state)


# Startup
load_rgb()

network.hostname("pico-light")
wlan = network.WLAN(network.STA_IF)

wlan.active(True)
wlan.connect("dssh4411", "dan65slo94sky98")

while not wlan.isconnected() and wlan.status() >= 0:
    print("Waiting to connect...")
    time.sleep(1)

print(f"IP: {wlan.ifconfig()[0]}")
while True:
    try:
        app.run(port=80)
    except Exception as e:
        print(f"Error running server: {e}")
        time.sleep(1)
