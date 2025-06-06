import machine

i2c1 = machine.I2C(1)
i2c3 = machine.I2C(3)

knownDevices = {
  '0x18' : 'rak1904 proto / lis3dh', # proto is 0x18
  '0x19' : 'rak1904 / lis3dh',
  '0x2c' : 'rak12008 / stc31',
  '0x42' : 'rak12500 / gnss',
  '0x76' : 'rak1906 / bme680',
  '0x59' : 'rak12047 / sgp40',
  '0x5c' : 'rak1902 / lps22hb',
  '0x44' : 'rak1903 / opt3001',
  '0x53' : 'rak12019 / ltr-390uv-01',
  '0x68' : 'MPU6050',
}

def showDevices():
  global knownDevices, devices
  if len(devices) == 0:
    print("No i2c device !")
  else:
    print('i2c devices found:', len(devices))
    for device in devices:
      dn = hex(device)
      deviceType = knownDevices.get(dn)
      if deviceType == None:
          deviceType = 'Unknown'
      print(" . Address: ", dn, "|", deviceType)

print('Scan i2c bus 1...')
devices = i2c1.scan()
showDevices()

print('Scan i2c bus 3...')
devices = i2c3.scan()
showDevices()
