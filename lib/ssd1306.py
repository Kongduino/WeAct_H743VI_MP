# MicroPython SSD1306 OLED driver, I2C and SPI interfaces
# https://github.com/stlehmann/micropython-ssd1306

from micropython import const
import framebuf, gc

# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORMAL_DISPLAY = const(0xA6)
SET_INVERT_DISPLAY = const(0xA7)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # address setting
            SET_MEM_ADDR,
            0x00,  # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc
            # display
            SET_CONTRAST,
            0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORMAL_DISPLAY,  # not inverted
            # charge pump
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORMAL_DISPLAY | (invert & 1))

    def reverse_Bits(self, n):
        result = 0
        for i in range(8):
            result <<= 1
            result |= n & 1
            n >>= 1
        return result

    def scrollUp(self, start = 0):
        # works with the regular 8x8 font
        # 1 line = 8 bits
        # start = first line to scroll
        # display.scrollUp(1) ==> Leaves line 0 alone
        start = start * 128
        size = len(self.buffer) - start
        for i in range(start, size):
            self.buffer[i] = self.buffer[i+128]
        for i in range(0, 128):
            self.buffer[len(self.buffer)-i-1] = 0

    def rotateBuffer(self):
        # 180° rotation
        # Reverses the buffer AND each byte
        size = len(self.buffer) // 2
        for i in range(0, size):
            a = self.reverse_Bits(self.buffer[i])
            ix = int((size*2)-i-1)
            self.buffer[i] = self.reverse_Bits(self.buffer[ix])
            self.buffer[ix] = a

    def drawGlyph(self, fontDefs, char, px, py):
        #Defs = [Mono12glyph, Mono12Bitmaps, first, last, yAdvance]
        bitmaps = fontDefs[1]
        first = fontDefs[2]
        last = fontDefs[3]
        yAdvance = fontDefs[4]
        if char < first or char > last:
            return
        glyph = fontDefs[0][char - first]
        width = glyph[1]
        if width + px >= self.width:
            return False
        height = glyph[2] 
        numBytes = width * height
        nBytes = numBytes // 8
        if nBytes*8 < numBytes:
            nBytes += 1
        payload = bitmaps[glyph[0]:glyph[0]+nBytes]
        myString = ''
        for x in payload:
            a='0000000'+bin(x)[2:]
            myString += a[-8:]
        ix = 0
        iy = 0
        xOffset = glyph[4]
        yOffset = glyph[2] + glyph[5]
        yOffset = yAdvance + glyph[5]
        for n in range(0, numBytes):
            if myString[n] == '1':
                self.pixel(px+ix+xOffset, py+iy+yOffset, 1)
            ix += 1
            if ix == width:
                ix = 0
                iy += 1
        return px + glyph[3]

    def displayString(self, fontDefs, text, px, py, wrapAround = True):
        if px < 0:
            sw = self.stringWidth(fontDefs, text)
            if px == -1:
                # center string
                px = (self.width - sw) // 2
            elif px == -2:
                # right-aligned
                px = (self.width - sw)
            if px < 0:
                # Just in case...
                px = 0
        if py == -2:
            # bottom aligned
            py = self.height - fontDefs[4] - 1
        elif py == -1:
            # vertically centered
            py = (self.height - fontDefs[4]) // 2 - 1
        for c in text:
            rslt = self.drawGlyph(fontDefs, ord(c), px, py)
            if rslt == False:
                if wrapAround == False:
                    return
                px = 0
                py += fontDefs[4]
                if py >= self.height:
                    return
                rslt = self.drawGlyph(fontDefs, ord(c), px, py)
                px = self.drawGlyph(fontDefs, ord(c), px, py)
            else:
                px = rslt
        gc.collect()

    def glyphWidth(self, fontDefs, char):
        #Defs = [Mono12glyph, Mono12Bitmaps, first, last, yAdvance]
        if char < fontDefs[2] or char > fontDefs[3]:
            return 0
        glyph = fontDefs[0][char - fontDefs[2]]
        return glyph[3]

    def stringWidth(self, fontDefs, text):
        #Defs = [Mono12glyph, Mono12Bitmaps, first, last, yAdvance]
        rslt = 0
        for c in text:
            rslt += self.glyphWidth(fontDefs, ord(c))
        return rslt

    def cls(self):
        self.fill(0)
        self.show()

    def doubleText(self, line):
        pyStart = line * 8
        fbuf = framebuf.FrameBuffer(bytearray(128 * 2), 128, 16, framebuf.MONO_VLSB)
        px = 0 # could add a variable start position
        py = 0
        for y in range(0, 8):
            py = y*2
            for x in range(0, 64):
                px = x*2
                c = self.pixel(x, pyStart+y)
                if c == 1:
                    fbuf.pixel(px, py, 1)
                    fbuf.pixel(px+1, py, 1)
                    fbuf.pixel(px, py+1, 1)
                    fbuf.pixel(px+1, py+1, 1)
        self.blit(fbuf, 0, line*8)

    def show(self, rotate180 = False):
        if rotate180 == True:
            self.rotateBuffer()
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)
        if rotate180 == True:
            self.rotateBuffer()

class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc = False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)

    def setContrast(self, uContrast):
        # one command only. Faster.
        d = int(uContrast) & 0xFF
        self.i2c.writeto(self.addr, bytearray([0x00, SET_CONTRAST, d]))

class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        self.rate = 10 * 1024 * 1024
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        import time
        self.res(1)
        time.sleep_ms(1)
        self.res(0)
        time.sleep_ms(10)
        self.res(1)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
