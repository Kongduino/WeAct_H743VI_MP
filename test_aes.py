from kongduino import *
import time, random
from machine import SPI, Pin
from st7735 import TFT, TFTColor
from sysfont import sysfont
import cryptolib, binascii

spi = SPI(4, baudrate=12000000)
aDC = Pin("PE13")
aReset = None
aCS = Pin("PE11")
LCD_LED = Pin("PE10", Pin.OUT)
LCD_LED.off()
tft=TFT(spi, aDC, aReset, aCS)
tft.initr()
tft.rgb(True)
tft.invertcolor(True)
tft.fill(TFT.BLACK)
f=open('/flash/Images/KduinoLogo.b16', 'rb')
w = int.from_bytes(f.read(2), 'little')
h = int.from_bytes(f.read(2), 'little')
tft._setwindowloc((0,0),(w - 1,h - 1))
tft.dc(1)
tft.cs(0)
for row in range(h):
  row = f.read(2 * w)
  tft.spi.write(row) # send one row
tft.cs(1) # display
f.close()
tft.rotation(0)

tft.text((30, 130), "Setup", TFT.WHITE, sysfont, 1, True)
randomBuff = bytearray(96)
for i in range(0, 96):
    randomBuff[i] = random.randint(0, 255)

print("> randomBuff")
hexdump(randomBuff)
pKey = randomBuff[0:16]
pIV = randomBuff[16:32]
plaintext = randomBuff[32:96]
print("> Key")
hexdump(pKey)
print("> IV")
hexdump(pIV)
print("> Plaintext")
hexdump(plaintext)

tft.text((30, 140), "Encrypt", TFT.WHITE, sysfont, 1, True)
print("Software AES")
buffer = plaintext
goal = time.ticks_ms() + 3000
count = 0
while time.ticks_ms() < goal:
    result = encryptAES_CBC(buffer, pKey, pIV)
    count += 1
count = int(count/3)
print("Encryption: {} rounds / second".format(count))

tft.text((30, 130), "Decrypt", TFT.WHITE, sysfont, 1, True)
goal = time.ticks_ms() + 3000
count = 0
while time.ticks_ms() < goal:
    result = decryptAES_CBC(buffer, pKey, pIV)
    count += 1
count = int(count/3)
print("Decryption: {} rounds / second".format(count))

plaintext = randomBuff[32:96]
buffer = plaintext
result = encryptAES_CBC(buffer, pKey, pIV)
print("> Ciphertext")
hexdump(buffer)
result = decryptAES_CBC(buffer, pKey, pIV)
print("> Deciphered")
hexdump(buffer)

if buffer[0:64] == plaintext[0:64]:
    print("[√] AES test successful")
    tft.text((30, 140), "Success ", TFT.WHITE, sysfont, 1, True)
else:
    print("[X] AES test failed")
    tft.text((30, 140), "Fail    ", TFT.WHITE, sysfont, 1, True)

crc0 = crc(plaintext)
crc1 = crc(buffer)
if crc0 == crc1:
    print("[√] CRC test successful")
else:
    print("[X] CRC test failed")
#spi.deinit()

print("\nCryptolib")
buffer = plaintext
goal = time.ticks_ms() + 3000
count = 0
while time.ticks_ms() < goal:
    a = cryptolib.aes(pKey, 2, pIV)
    result = a.encrypt(buffer)
    count += 1
count = int(count/3)
print("Encryption: {} rounds / second".format(count))

buffer = plaintext
goal = time.ticks_ms() + 3000
count = 0
while time.ticks_ms() < goal:
    a = cryptolib.aes(pKey, 2, pIV)
    result = a.decrypt(buffer)
    count += 1
count = int(count/3)
print("Encryption: {} rounds / second".format(count))

buffer = plaintext
a = cryptolib.aes(pKey, 2, pIV)
b = cryptolib.aes(pKey, 2, pIV)
encrypted = a.encrypt(buffer)
decrypted = b.decrypt(encrypted)
print("> Ciphertext")
hexdump(encrypted)
print("> Deciphered")
hexdump(decrypted)
if decrypted[0:64] == plaintext[0:64]:
    print("[√] AES test successful")
else:
    print("[X] AES test failed")
crc2 = binascii.crc32(plaintext)
crc3 = binascii.crc32(buffer)
if crc0 == crc1:
    print("[√] CRC test successful")
else:
    print("[X] CRC test failed")
if crc0 == crc2:
    print("[√] kongduino vs binascii CRC test successful")
else:
    print("[X] kongduino vs binascii CRC test failed")
