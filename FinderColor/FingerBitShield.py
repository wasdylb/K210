from machine import I2C

K210i2c = I2C(I2C.I2C0, freq=100000, scl=34, sda=35)

MOTORPRO_ADDRESS = 0x73

BIT_14 = 14
BIT_13 = 13
BIT_12 = 12
BIT_11 = 11
BIT_10 = 10
BIT_9 = 9
BIT_8 = 8

ADDR16_SPEED1 = 0x00
ADDR16_SPEED2 = 0x01
ADDR8_FAULT = 0x04
ADDR8_VERSION = 0x1F
ADDR8_RESET = 0x20

FREE = 0  # 释放
BRAKE = 20000  # 刹车


class motorPro(object):
    def __init__(self, i2c=K210i2c, address=MOTORPRO_ADDRESS, _bit=BIT_8):
        self.devAddr = address
        _bit = self.constrain(_bit, BIT_8, BIT_14)
        self.multiple = 0x4000 >> _bit
        self.speedRange = 1 << _bit - 1
        self.i2c = K210i2c

    def constrain(self, val, min_val, max_val):
        if val < min_val:
            return min_val
        if val > max_val:
            return max_val
        return val

    def begin(self):
        return self.i2c.is_ready(self.devAddr)

    def write16(self, _writeAddr, buf, _len):
        _buf = bytearray(_len * 2)
        for i in range(0, _len):
            _buf[2 * i] = buf >> 8
            _buf[2 * i + 1] = buf & 0xFF
        self.i2c.writeto_mem(self.devAddr, _writeAddr, _buf)

    def setSpeed1(self, _speed):
        if _speed == BRAKE:
            speedBuf = _speed
        else:
            _speed = self.constrain(_speed, -self.speedRange, self.speedRange)
            speedBuf = -_speed * self.multiple
        self.write16(ADDR16_SPEED1 * 2, speedBuf, 1)

    def setSpeed2(self, _speed):
        if _speed == BRAKE:
            speedBuf = _speed
        else:
            _speed = self.constrain(_speed, -self.speedRange, self.speedRange)
            speedBuf = _speed * self.multiple
        self.write16(ADDR16_SPEED2 * 2, speedBuf, 1)

    def setSpeed(self, _speedL, _speedR):
        self.setSpeed1(_speedL)
        self.setSpeed2(_speedR)
