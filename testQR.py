import kongduino
from st7735 import TFT, TFTColor
from sysfont import sysfont
from machine import SPI, Pin

spi = SPI(4, baudrate = 20000000)
aDC = Pin("PE13")
aReset = None
aCS = Pin("PE11")
LCD_LED = Pin("PE10", Pin.OUT)
LCD_LED.off()
tft=TFT(spi, aDC, aReset, aCS)
tft.initr()
tft.rgb(True)
tft.rotation(2)
tft.invertcolor(True)
tft.fill(TFT.WHITE)

def getBit(x, i):
  return ((x >> i) & 1) != 0

def getModuleBounded(qrcode, x, y):
    qrsize = qrcode[0]
    index = y * qrsize + x
    return getBit(qrcode[(index >> 3) + 1], index & 7)

def qrcodegen_getModule(qrcode, x, y):
    qrsize = qrcode[0]
    return getModuleBounded(qrcode, x, y)

qr0 = bytearray(3920)
size = kongduino.genText2(b"This is wonderful text that should scan properly\x00", qr0, 40)
print(f"Code size: {size}")
for y in range(0, size):
    s = ""
    for x in range(0, size):
        if qrcodegen_getModule(qr0, x, y):
            s += '⬛️️'
            tft.fillrect((35+x*2, 10+y*2), (2, 2), TFT.BLACK)
            #tft.pixel((40+x, 40+y), TFT.BLACK)
        else:
            s += '▫️'
        #    tft.fillrect((x*4, y*4), (4, 4), TFT.WHITE)
    print(s)