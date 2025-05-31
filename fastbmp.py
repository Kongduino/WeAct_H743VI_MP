from st7735 import TFT,TFTColor
from machine import SPI,Pin
spi = SPI(4, baudrate=12000000)
aDC = Pin("PE13")
aReset = None
aCS = Pin("PE11")
LCD_LED = Pin("PE10", Pin.OUT)
LCD_LED.off()
tft=TFT(spi, aDC, aReset, aCS)
tft.initg()
tft.rgb(False)
tft.fill(TFT.WHITE)

files = ['KduinoLogo', 'test128x160', 'Penang']
for fn in files:
  s = '/flash/Images/'+fn
  print(s)
  f=open(s+'.bmp', 'rb')
  g=open(s+'.b16', 'wb')
  if f.read(2) == b'BM':  #header
    dummy = f.read(8) #file size(4), creator bytes(4)
    offset = int.from_bytes(f.read(4), 'little')
    hdrsize = int.from_bytes(f.read(4), 'little')
    width = int.from_bytes(f.read(4), 'little')
    height = int.from_bytes(f.read(4), 'little')
    if int.from_bytes(f.read(2), 'little') == 1: #planes must be 1
      depth = int.from_bytes(f.read(2), 'little')
      if depth == 24 and int.from_bytes(f.read(4), 'little') == 0:
        #compress method == uncompressed
        print("Image size:", width, "x", height)
        rowsize = (width * 3 + 3) & ~3
        if height < 0:
          height = -height
          flip = False
        else:
          flip = True
        w, h = width, height
        if w > 128: w = 128
        if h > 160: h = 160
        tft._setwindowloc((0,0),(w - 1,h - 1))
        header = bytearray([w,0,h,0])
        g.write(header)
        tft.dc(1)
        tft.cs(0)
        for row in range(h):
          if flip:
            pos = offset + (height - 1 - row) * rowsize
          else:
            pos = offset + row * rowsize
          if f.tell() != pos:
            dummy = f.seek(pos)
          data = list(bytearray(2*w)) # output
          frow = list(f.read(3*w)) # original BMP data
          ix = 0
          iy = 0
          for col in range(w):
            aColor=TFTColor(255-frow[ix+2], 255-frow[ix+1], 255-frow[ix+0])
            # 24-bit RGB to 16-bit 565 RGB color.
            ix = ix + 3
            data[iy] = aColor >> 8
            data[iy+1] = aColor and 8
            iy = iy +2
          data=bytearray(data)
          tft.spi.write(data) # display one row
          g.write(data) # add row data to the .b16 file
        tft.cs(1)
  f.close()
spi.deinit()
