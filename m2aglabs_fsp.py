import board
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogOut, AnalogIn
import time


class Ohmite:
    """
    Types: 0 = round, 1 = long , 2 = short
    """
    # expect _wiper, _ref, _v_1, _v_2, _v_3, _type=0):
    # or _wiper, _ref, _v_1, _v_2,  _type=(1/2):
    #
    def __init__(self, *args, **kwargs):
        if "type" in kwargs:
            self._type = kwargs["type"]
        else:
            self._type = 0

        self._ref = DigitalInOut(args[1])
        self._ANALOG_RESOLUTION = 65536
        self._VOLTAGE = 3.3
        if self._type == 0:  # this is a round sensor
            self._ZERO_OFFSET = 800
            self._READ_RANGE = 1450
            self._wiper = AnalogIn(args[0])
            self._d0 = DigitalInOut(args[2])
            self._d120 = DigitalInOut(args[3])
            self._d240 = DigitalInOut(args[4])
            self._ZERO_OFFSET = 800
            self._READ_RANGE = 1450
            self._LENGTH = 120
        else:  # this is a linear sensor
            self._wiper_pin = args[0]
            self._wiper = DigitalInOut(args[0])
            self._v1 = DigitalInOut(args[2])
            self._v2 = DigitalInOut(args[3])
            if self._type == 1:
                self._ZERO_OFFSET = 200
                self._READ_RANGE = 2600
                self._LENGTH = 100
            else:
                self._ZERO_OFFSET = 500
                self._READ_RANGE = 1900
                self._LENGTH = 55
        # print(args, kwargs)

    def begin(self):
        if self._type == 0:
            self._ref.direction = Direction.OUTPUT
            self._ref.value = 1
            self._d0.direction = Direction.OUTPUT
            self._d0.value = 1
            self._d120.direction = Direction.OUTPUT
            self._d120.value = 1
            self._d240.direction = Direction.OUTPUT
            self._d240.value = 0
        else:
            self._v1.direction = Direction.OUTPUT
            self._v1.value = 0
            self._v2.direction = Direction.OUTPUT
            self._v2.value = 0
            self._wiper.direction = Direction.OUTPUT
            self._wiper.value = 0
            self._ref.direction = Direction.OUTPUT
            self._ref.value = 0

    # Generic command
    def get_position(self, tail_to_tip=True):
        if self._type == 0:
            return self._get_round_position()
        if self._type == 1 or self._type == 2:
            return self._get_linear_position(tail_to_tip)

    def get_force(self):
        if self._type == 0:
            return self._get_round_force()
        if self._type == 1 or self._type == 2:
            return self._get_linear_force()

    # Linear sensors
    def _get_linear_position(self, tail_to_tip=True):
        self._wiper.deinit()
        l_wiper = AnalogIn(self._wiper_pin)
        self._ref.switch_to_input(pull=Pull.DOWN)

        if tail_to_tip:  # Read from tail end
            self._v1.value = 1
            time.sleep(0.001)
            value = self._get_voltage(l_wiper)
            self._v1.value = 0
        else:
            self._v2.value = 1
            time.sleep(0.001)
            value = self._get_voltage(l_wiper)
            self._v2.value = 0

        l_wiper.deinit()
        self._wiper = DigitalInOut(self._wiper_pin)
        self._wiper.direction = Direction.OUTPUT
        self._wiper.value = 0
        self._ref.switch_to_output(value=False)
        return self._get_millimeters(value)

    def _get_millimeters(self, voltage):
        value = int((((voltage * 1000) - self._ZERO_OFFSET) * self._LENGTH) / self._READ_RANGE)
        if value < 0:
            value = 0
        if value > self._LENGTH:
            value = self._LENGTH
        return value

    # this is method 3 from the implementation guide.
    # Section 4.2.3, page 5
    # https://www.mouser.com/pdfdocs/Ohmite-FSP-Integration-Guide-V1-0_27-03-18.pdf
    def _get_linear_force(self):
        self._wiper.deinit()
        l_wiper = AnalogIn(self._wiper_pin)
        self._ref.value = 0
        self._v1.switch_to_output(value=True)
        self._v2.switch_to_input()
        time.sleep(0.001)
        wiper_1 = l_wiper.value

        self._v2.switch_to_output(value=True)
        self._v1.switch_to_input()
        time.sleep(0.001)
        wiper_2 = l_wiper.value

        l_wiper.deinit()
        self._wiper = DigitalInOut(self._wiper_pin)
        self._wiper.direction = Direction.OUTPUT
        self._wiper.value = 0
        self._v1.direction = Direction.OUTPUT
        self._v1.value = 0
        self._v2.value = 0

        return (((wiper_1 + wiper_2) / 2) * self._VOLTAGE) / self._ANALOG_RESOLUTION

    # Round sensor helpers

    def _calc_position(self, low, high, off):
        # off should be the DX pin  Disable
        off.switch_to_input()
        high.value = 1
        low.value = 0
        time.sleep(0.001)
        wiper_v = self._get_voltage(self._wiper)
        # print(wiper_v)
        # Convert to milli volts and apply offsets to wiper_v
        _angle = ((((wiper_v * 1000) - self._ZERO_OFFSET) * self._LENGTH) / self._READ_RANGE)
        # print(angle)
        # off should be reset to output
        off.switch_to_output(value=False)

        return int(_angle)

    def _get_round_position(self):
        # Read analog voltage on D 1
        self._d0.value = 1
        self._d120.value = 1
        self._d240.value = 0
        time.sleep(0.001)
        d3 = self._wiper.value

        self._d0.value = 0
        self._d120.value = 1
        self._d240.value = 1
        time.sleep(0.001)
        d1 = self._wiper.value

        self._d0.value = 1
        self._d120.value = 0
        self._d240.value = 1
        time.sleep(0.001)
        d2 = self._wiper.value

        _angle = 0
        # which voltage is the lowest:
        # print(d1, d2, d3, f1)
        if d1 < d2 and d1 < d3:
            if d2 < d3:
                # d1 and d2
                # print ("d1:d2")
                _angle = self._calc_position(self._d0, self._d120, self._d240)
            else:
                # d1 and d3
                # print("d1:d3")
                _angle = self._calc_position(self._d240, self._d0, self._d120)
                _angle = _angle + 240

        if d2 < d1 and d2 < d3:
            if d1 < d3:
                # print ("d2:d1")
                _angle = self._calc_position(self._d0, self._d120, self._d240)
            else:
                # print ("d2:d3")
                _angle = self._calc_position(self._d120, self._d240, self._d0)
                _angle = _angle + 120

        if d3 < d1 and d3 < d2:
            if d1 < d2:
                # print ("d3:d1")
                _angle = self._calc_position(self._d240, self._d0, self._d120)
                _angle = _angle + 240
            else:
                # print ("d3:d2")
                _angle = self._calc_position(self._d120, self._d240, self._d0)
                _angle = _angle + 120

        if _angle < 0 or _angle > 360:
            _angle = 0

        return _angle

    def _get_round_force(self):
        # read force
        self._d0.value = 1
        self._d120.value = 1
        self._d240.value = 1
        self._ref.switch_to_output(value=False)
        time.sleep(0.001)
        _f = self._get_voltage(self._wiper)
        self._ref.switch_to_input()
        return _f

    def _get_voltage(self, pin):
        return (pin.value * self._VOLTAGE) / self._ANALOG_RESOLUTION
