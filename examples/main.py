import board
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogOut, AnalogIn
# from adafruit_hid.keyboard import Keyboard
# from adafruit_hid.keycode import Keycode
# from adafruit_hid.mouse import Mouse
import time
import neopixel
from m2aglabs_fsp import Ohmite

# Round sensor (FSP03CE) -- it needs a lot of inputs
wiper = board.A5
v_ref = board.D0
D_0 = board.D2
D_120 = board.D1
D_240 = board.D3

# Long linear sensor (FSP01CE)
l_wiper = board.A4
l_ref = board.D5
l_v1 = board.D4
l_v2 = board.D9

# Long linear sensor (FSP02CE)
s_wiper = board.A2
s_ref = board.D7
s_v1 = board.D6
s_v2 = board.D10

s_lin = Ohmite(s_wiper, s_ref, s_v1, s_v2, type=2)
l_lin = Ohmite(l_wiper, l_ref, l_v1, l_v2, type=1)
s_rnd = Ohmite(wiper, v_ref, D_0, D_120, D_240)

# NeoPixel strip (of 16 LEDs) connected on D4
NUMPIXELS = 1
pixels = neopixel.NeoPixel(board.NEOPIXEL, NUMPIXELS, brightness=0.01, auto_write=False)


# pixels = neopixel.NeoPixel(board.NEOPIXEL, NUMPIXELS, auto_write=False)


# Used if we do HID output, see below
# kbd = Keyboard()
# mouse = Mouse()
######################### HELPERS ##############################


# Helper to give us a nice color swirl
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0:
        return 0, 0, 0
    if pos > 255:
        return 0, 0, 0
    if pos < 85:
        return int(pos * 3), int(255 - (pos * 3)), 0
    elif pos < 170:
        pos -= 85
        return int(255 - pos * 3), 0, int(pos * 3)
    else:
        pos -= 170
        return 0, int(pos * 3), int(255 - pos * 3)


######################### MAIN LOOP ##############################

s_rnd.begin()
l_lin.begin()
s_lin.begin()
i = 0
while True:

    s_force = s_lin.get_force()
    force = s_rnd.get_force()
    l_force = l_lin.get_force()

    if s_force > 0.4:
        position = s_lin.get_position(False)
        print(s_force, position)
        pixels[0] = wheel(position)
        pixels.show()
    # for long linear
    elif l_force > 0.4:
        position = l_lin.get_position()
        print(l_force, position)
        pixels[0] = wheel(position)
        pixels.show()
        # for round sensor
    elif force > 0.09:
        angle = s_rnd.get_position()
        print(force, angle)
        pixels[0] = wheel(angle % 256)
        pixels.show()
    else:
        i = (i + 1) % 256  # run from 0 to 255
        pixels[0] = wheel(i)
        pixels.show()
        time.sleep(0.001)  # make bigger to slow down

