from aes_lib import *
from hexdump import hexDump
import time, random

randomBuff = bytearray(112)
for i in range(0, 112):
    randomBuff[i] = random.randint(0, 255)

pKey = randomBuff[0:32]
pIV = randomBuff[32:48]
#plaintext = "this is a random sentence..."
#plaintext = bytearray(plaintext.encode())
plaintext = randomBuff[48:112]
print("> Key")
hexDump(pKey)
print("> IV")
hexDump(pIV)
print("> Plaintext")
hexDump(plaintext)

goal = time.ticks_ms() + 1000
count = 0
while time.ticks_ms() < goal:
    encrypt = cbc_encryptor(pKey, pIV, plaintext)
    count += 1
print("Encryption: {} rounds per second".format(count))

goal = time.ticks_ms() + 1000
count = 0
while time.ticks_ms() < goal:
    decrypt = cbc_decryptor(pKey, encrypt.ciphertext)
    count += 1
print("Decryption: {} rounds per second".format(count))

print("> Ciphertext")
hexDump(encrypt.ciphertext)
print("> Deciphered")
hexDump(decrypt.plaintext)
if decrypt.plaintext[0:64] == plaintext[0:64]:
    print("[√] Test successful!")
else:
    print("[x] Test failed!")
