import lzw, random, json, binascii
from aes_lib import *
from hexdump import hexDump
from machine import Pin, ADC

rnd = ADC(Pin("PC3"))
x = rnd.read_u16()
x = rnd.read_u16()
x = rnd.read_u16()
x = rnd.read_u16()
random.seed(x)

def getRandomByte():
    x = 0
    for j in range (0, 8):
        b = random.randint(0, 255) & 0b00000001
        while (b == random.randint(0, 255) & 0b00000001):
            # von Neumann extractor.
            z = random.randint(0, 255)
        x = (x << 1) | b
    return x

def getRandomWord():
    return getRandomByte() << 8 | getRandomByte()

temp = (getRandomByte() % 130) / 10.0 + 12
hum = getRandomByte() / 10.0
press = getRandomWord() % 120 + 900
a=bytearray(4)
for i in range(0, 4):
    a[i] = getRandomByte()
UUID = binascii.hexlify(a).decode() 
packet = {}
packet['temp'] = temp
packet['hum'] = hum
packet['press'] = press
packet['msgID'] = UUID

msg = json.dumps(packet).replace(' ','')
print(msg)
pkt = lzw.compress(msg)
print(pkt)
s1 = len(pkt)
s0 = len(msg)
ratio = (1 - (s1 / s0))*100
print("Compression: {} vs {} bytes, ie {:.2f}%".format(s1, s0, ratio))

pIV = bytearray(16)
for i in range(0, 16):
    pIV[i] = getRandomByte()
pKey = bytearray(32)
for i in range(0, 32):
    pKey[i] = getRandomByte()
print("> Key")
hexDump(pKey)
print("> IV")
hexDump(pIV)
print("> Plaintext")
hexDump(pkt)

encrypt = cbc_encryptor(pKey, pIV, pkt)
decrypt = cbc_decryptor(pKey, encrypt.ciphertext)

print("> Ciphertext")
hexDump(encrypt.ciphertext)
print("> Deciphered")
pkt = lzw.decompress(decrypt.plaintext[0:len(pkt)])
hexDump(pkt.encode())
print(msg == pkt)
pkt0 = json.loads(pkt)
for x in pkt0:
    print("{}: {}".format(x, pkt0[x]))

