#!/usr/bin/env python3
"""
Based on...
SquishBox Raspberry Pi FluidPatcher interface
"""

__version__ = '0.0.1'

import sys, glob, re
import subprocess
from pathlib import Path
import threading
import serial
import time
import traceback

import RPi.GPIO as GPIO

# Stuff for Nokia Display
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
from PIL import ImageDraw
from PIL import Image
from PIL import ImageFont

# Uart (how Pi talks to Pico)

ser = serial.Serial('/dev/ttyS0', 4800)
ser.write(b'HiHi\n')

# Raspberry Pi hardware SPI config (for Nokia display):
DC = 23
RST = 24
SPI_PORT = 0
SPI_DEVICE = 0

# squishbox stompswitch
STOMP_MIDICHANNEL = 16
STOMP_MOMENT_CC = 30
STOMP_TOGGLE_CC = 31

# RPi GPIO pin numbers (BCM numbering) for different hardware versions
ACTIVE = GPIO.LOW

PIN_OUT = 12, 16, 26 # additional free pins - see SquishBox.gpio_set()
ROT_L = 22; ROT_R = 10; BTN_R = 9                # rotary encoder R/L pins + button
BTN_SW = 27; PIN_LED = 17                        # stompbutton and LED

# adjust timings/values below as needed/desired
HOLD_TIME = 1.0
MENU_TIMEOUT = 5.0
BLINK_TIME = 0.1
SCROLL_TIME = 0.4
SCROLL_PAUSE = 4
POLL_TIME = 0.01
BOUNCE_TIME = 0.02
COLS, ROWS = 16, 2

# button states
UP = 0; DOWN = 1; HELD = 2
# events
NULL = 0; DEC = 1; INC = 2; SELECT = 3; ESCAPE = 4


class SquishBox():
    """An interface for RPi using character LCD and buttons"""

    def nokia_print(self, newline):
        self.nokia_lines.append(newline)
        #disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
        #disp.begin(contrast=40)
        self.disp.clear()
        #font = ImageFont.load_default()
        image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
        for idx, line in enumerate(self.nokia_lines[-5:]):
        #draw.text((1,1), 'Starting.', font=font)
            draw.text((1,idx*8), line, font=self.font)
        self.disp.image(image)
        self.disp.display()
    def nokia_clear(self):
        self.nokia_lines = []
        self.disp.clear()
        self.disp.display()

    def __init__(self):
        """Initializes the LCD and GPIO
        
        Attributes:
          buttoncallback: When the state of a button connected to BTN_SW
            changes, this function is called with 1 if the button was
            pressed, 0 if it was released.
          wificon: contains either the WIFIUP or WIFIDOWN character
            depending on the last-known status of the wifi adapter
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        #for chan in (ROT_R, ROT_L, BTN_R, BTN_SW):
        for chan in (BTN_R, BTN_SW):
            if chan:
                pud = GPIO.PUD_UP if ACTIVE == GPIO.LOW else GPIO.PUD_DOWN
                GPIO.setup(chan, GPIO.IN, pull_up_down=pud)
        #for chan in (LCD_RS, LCD_EN, *LCD_DATA, *PIN_OUT):
            #if chan:
                #GPIO.setup(chan, GPIO.OUT)
        for btn in (BTN_R, BTN_SW):
            if btn:
                GPIO.add_event_detect(btn, GPIO.BOTH, callback=self._button_event)
        #for enc in (ROT_L, ROT_R):
            #if enc:
                #GPIO.add_event_detect(enc, GPIO.BOTH, callback=self._encoder_event)
        self.state = {BTN_R: UP, BTN_SW: UP}
        self.timer = {BTN_R: 0, BTN_SW: 0}
        #self.encstate = 0b000000
        #self.encvalue = 0
        self.buttoncallback = None

        self.nokia_lines = []
        self.disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
        self.disp.begin(contrast=40)
        self.font = ImageFont.load_default()
        self.nokia_print("Starting")

        #for val in (0x33, 0x32, 0x28, 0x0c, 0x06):
            #self._lcd_send(val)
        #self.lcd_clear()
        #for loc, bits in enumerate(charbits):
            #self._lcd_send(0x40 | loc << 3)
            #for row in bits:
                #self._lcd_send(row, 1)

        #self.wificon = WIFIDOWN
        #self.wifi_state()
        #sys.excepthook = lambda etype, err, tb: self.display_error(err, etype=etype, tb=tb)

    def update(self, idle=POLL_TIME, callback=True):
        """Polls buttons and updates LCD
        
        Call in the main loop of a program to poll the buttons and rotary
        encoder, and update the LCD if necessary. Sleeps for a small amount
        of time before returning so other processes can run.
        Returns an event code based on the state of the buttons. If
        buttoncallback is set and callback=True, the stompswitch calls
        that function instead of sending an event.

        * NULL (0) - no event
        * DEC (1) - stompswitch tapped or encoder rotated counter-clockwise
        * INC (2) - encoder button tapped or encoder rotated clockwise
        * SELECT (3) - encoder button held for HOLD_TIME seconds
        * ESCAPE (4) - stompswitch held for HOLD_TIME seconds

        Args:
          idle: number of seconds to sleep before returning
          callback: if False ignores buttoncallback

        Returns: an integer event code
        """
        callback = self.buttoncallback if callback else None
        t = time.time()
#        for r in range(ROWS):
#            text = list(self.buffer[r])
#            if len(text) > COLS:
#                if t > self.scrolltimer:
#                    self.scrollpos[r] += 1
#                    if self.scrollpos[r] > len(text) - COLS + SCROLL_PAUSE:
#                        self.scrollpos[r] = -SCROLL_PAUSE
#                i = max(0, self.scrollpos[r])
#                i = min(i, len(text) - COLS)
#                text = text[i : i+COLS]
#            if self.blinktimer > 0:
#                for i, c in enumerate(self.blinked[r]):
#                    if c:
#                        text[i] = c
#            self._lcd_putchars(text, r, 0)
#        if t > self.scrolltimer:
#            self.scrolltimer = time.time() + SCROLL_TIME
#        if t > self.blinktimer:
#            self.blinked = [[""] * COLS for _ in range(ROWS)]
#            self.blinktimer = 0
        event = NULL
#        for b in BTN_R, BTN_SW:
#            if t - self.timer[b] > BOUNCE_TIME:
#                if GPIO.input(b) == ACTIVE:
#                    if self.state[b] == UP:
#                        self.state[b] = DOWN
#                        if b == BTN_SW and callback:
#                            callback(1)
#                    elif self.state[b] == DOWN and t - self.timer[b] >= HOLD_TIME:
#                        self.state[b] = HELD
#                        if b == BTN_R: event = SELECT
#                        elif b == BTN_SW and not callback: event = ESCAPE
#                else:
#                    if self.state[b] != UP and b == BTN_SW and callback:
#                        callback(0)
#                    if self.state[b] == DOWN:
#                        if b == BTN_R: event = INC
#                        elif b == BTN_SW and not callback: event = DEC
#                    self.state[b] = UP
#        if self.encvalue > 0: event = INC
#        elif self.encvalue < 0: event = DEC
#        self.encvalue = 0
        time.sleep(idle)
        return event
        
    def lcd_clear(self):
        """Clear the LCD"""
        self.nokia_clear()
        #self._lcd_send(0x01)
        #self._lcd_setcursorpos(0, 0)
        #self.buffer = [" " * COLS for _ in range(ROWS)]
        #self.written = [[""] * COLS for _ in range(ROWS)]
        #self.blinked = [[""] * COLS for _ in range(ROWS)]
        #self.scrollpos = [0] * ROWS
        #self.scrolltimer = 0
        #self.blinktimer = 0
        #time.sleep(2e-3)

    def lcd_write(self, text, row, col=0, mode='', now=False):
        """Writes text to the LCD
        
        Writes text to the LCD starting at row, col. Characters are
        stored in a buffer until the user calls update(). Can be
        called with now=True if the LCD needs to be updated now,
        usually because another process would delay updates.

        Args:
          text: string to write
          row: the row at which to start writing
          col: the column at which to start writing
          mode: if 'ljust' or 'rjust' pad with spaces, 'scroll' scrolls
            text to the right if it is long enough, otherwise place text
            starting at row, col
          now: if True update LCD now
        """
        self.nokia_print(text)
#        if mode == 'scroll':
#            if len(text) > COLS:
#                self.buffer[row] = text
#                self.scrollpos[row] = -SCROLL_PAUSE
#            else:
#                mode = 'ljust'
#        if mode == 'ljust':
#            self.buffer[row] = text[:COLS].ljust(COLS)
#        elif mode == 'rjust':
#            self.buffer[row] = text[:COLS].rjust(COLS)
#        elif mode != 'scroll':
#            self.buffer[row] = (self.buffer[row][:col]
#                                + text[: COLS-col]
#                                + self.buffer[row][col+len(text) :])[:COLS]
#        if now: self.update(idle=0)

    def lcd_blink(self, text, row=0, col=0, delay=BLINK_TIME):
        """Blink a character/message on the LCD
        
        Write text on the LCD that disappears after a delay. Text
        written by lcd_write() will reappear. Calling this with
        an empty string removes any current blinks. If a blink
        is already in progress when this is called, the new one
        is ignored.
        
        Args:
          text: string to write, '' to clear blinks
          row: the row at which to place text
          col: the column at which to place text
          delay: time to wait before removing text
        """
#        if text == '':
#            self.blinked = [[""] * COLS for _ in range(ROWS)]
#            self.blinktimer = 0
#        elif self.blinktimer == 0:
#            for i, c in enumerate(text[: COLS-col]):
#                self.blinked[row][col + i] = c
#            self.blinktimer = time.time() + delay

    def progresswheel_start(self):
        """Shows an animation while another process runs
        
        Displays a spinning character in the lower right corner of the
        LCD that runs in a thread after this function returns, to give
        the user some feedback while a long-running process completes.
        """
        #self.spinning = True
        #self.spin = threading.Thread(target=self._progresswheel_spin)
        #self.spin.start()
    
    def progresswheel_stop(self):
        """Removes the spinning character"""
        #self.spinning = False
        #self.spin.join()

    def waitfortap(self, t=0):
        """Waits until a button is pressed or some time has passed
        
        Args:
          t: seconds to wait, if 0 wait forever

        Returns: True if button was pressed, False if time expired
        """
        return True
#        tstop = time.time() + t
#        while True:
#            if t and time.time() > tstop:
#                return False
#            if self.update(callback=False) != NULL:
#                return True

    def display_error(self, err, msg="", etype=None, tb=None):
        """Displays Exception text on the LCD
        
        Reformats the text of an Exception so it can be displayed on one
        line and scrolls it across the bottom row of the LCD, and also prints
        information to stdout. Waits for the user to press a button, then
        returns if possible.

        Args:
          err: the Exception
          msg: an optional error message
        """
        self.nokia_print(msg)
#        if etype == KeyboardInterrupt:
#            sys.exit()
#        err_oneline = msg + re.sub(' {2,}', ' ', re.sub('\n|\^', ' ', str(err)))
#        self.lcd_write(err_oneline, ROWS - 1, mode='scroll')
#        if msg: print(msg)
#        if tb:
#            traceback.print_exception(etype, err, tb)
#        else:
#            print(err)
#        self.waitfortap()

    @staticmethod
    def shell_cmd(cmd, **kwargs):
        """Executes a shell command and returns the output
        
        Uses subprocess.run to execute a shell command and returns the output
        as ascii with leading and trailing whitespace removed. Blocks until
        shell command has returned.
        
        Args:
          cmd: text of the command line to execute
          kwargs: additional keyword arguments passed to subprocess.run

        Returns: the stripped ascii STDOUT of the command
        """
        return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, shell=True,
                              encoding='ascii', **kwargs).stdout.strip()

    @staticmethod
    def gpio_set(pin, state):
        """Sets the state of a GPIO

        Sets a GPIO high or low, as long as it isn't being used by something
        else. PIN_OUT can be modified to add outputs, as long as they don't
        conflict with those defined above for the LCD, buttons, and GPIOs
        18, 19, and 21 (which are used by the DAC).

        Args:
          pin: pin number (BCM numbering)
          state: True for high, False for low
        """
        if pin in PIN_OUT:
            if state: GPIO.output(pin, GPIO.HIGH)
            else: GPIO.output(pin, GPIO.LOW)

    def wifi_state(self, setstate=''):
        """Checks or sets the state of the wifi adapter
        
        Turns the wifi adapter on or off, or simply returns its current
        state. Does not determine whether it has connected to a network,
        only that it is enabled or disabled.

        Args:
          setstate: 'block' or 'unblock' to set the state, or
            empty string to check current state

        Returns: 'blocked' or 'unblocked'
        """
        if setstate:
            self.shell_cmd(f"sudo rfkill {setstate} wifi")
            state = 'blocked' if setstate == 'block' else 'unblocked'
        else:
            state = self.shell_cmd("rfkill list wifi -o SOFT -rn")
        self.wificon = WIFIDOWN if state == 'blocked' else WIFIUP
        return state

    def wifi_settings(self):
        """Displays a wifi settings menu
        
        Shows the connection status and current IP address(es) of the Pi
        and a list of any available wifi networks. Allows the user to
        enable/disable wifi and enter passkeys for visible networks
        in order to connect.
        """
        self.lcd_clear()
        if ip := sb.shell_cmd("hostname -I"):
            self.lcd_write(f"Connected as {ip}", ROWS - 2, mode='scroll')
        else:
            self.lcd_write("Not connected", ROWS - 2, mode='ljust')
        if self.wifi_state() == 'blocked':
            if self.choose_opt(["Enable WiFi"], row=ROWS - 1) == 0:
                self.wifi_state('unblock')
        else:
            self.lcd_write("scanning ", ROWS - 1, mode='rjust', now=True)
            x = sb.shell_cmd("iw dev wlan0 link")
            ssid = "".join(re.findall('SSID: ([^\n]+)', x))
            opts = [CHECK + ssid] if ssid else []
            self.progresswheel_start()
            try: x = sb.shell_cmd("sudo iw wlan0 scan", timeout=15)
            except subprocess.TimeoutExpired: x = ""
            self.progresswheel_stop()
            networks = set(re.findall('SSID: ([^\n]+)', x))
            opts += [*(networks - {ssid}), "Disable WiFi"]
            j = self.choose_opt(opts, row=ROWS - 1, mode='scroll', timeout=-1)
            if j < 0: return
            elif opts[j] == "Disable WiFi":
                self.wifi_state('block')
            elif j >= 0:
                if CHECK in opts[j]: return
                self.lcd_write("Password:", ROWS - 2, mode='ljust')
                psk = self.char_input(charset = PRNCHARS)
                if psk == '': return
                self.lcd_clear()
                self.lcd_write(opts[j], ROWS - 2, mode='ljust')
                self.lcd_write("adding network ", ROWS - 1, mode='rjust', now=True)
                self.progresswheel_start()
                network = f'\nnetwork={{\n  ssid=\"{opts[j]}\"\n  psk=\"{psk}\"\n}}'
                sb.shell_cmd(f"echo {network} | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf")
                sb.shell_cmd("sudo systemctl restart dhcpcd")
                self.progresswheel_stop()
                self.wifi_settings()

    def _button_event(self, button):
        t = time.time()
        self.timer[button] = t


class FluidBox:
    """Manages a SquishBox interface to FluidPatcher"""

    def __init__(self):
        """Creates the FluidBox"""
        self.pno = 0
        self.buttonstate = 0
        fp.midi_callback = self.listener
        sb.buttoncallback = self.handle_buttonevent
        self.midi_connect()
        self.load_bank(fp.currentbank)
        while not fp.currentbank:
            self.load_bank()
        while True:
            self.patchmode()

    def handle_buttonevent(self, val):
        """Handles callback events when the stompbutton state changes
        
        Sends a momentary and toggling MIDI message, and toggles sets the LED
        to match the state of the toggle.
        """
        fp.send_event(f"cc:{STOMP_MIDICHANNEL}:{STOMP_MOMENT_CC}:{val}")
        if val:
            self.buttonstate ^= 1
            fp.send_event(f"cc:{STOMP_MIDICHANNEL}:{STOMP_TOGGLE_CC}:{self.buttonstate}")
            sb.gpio_set(PIN_LED, self.buttonstate)

    def listener(self, sig):
        """Handles MidiSignals from FluidPatcher
        
        Receives MidiSignal instances in response to incoming MIDI events
        or custom events triggered by router rules. MidiSignals for custom
        events have a `val` parameter that is the result of parameter
        routing, and additional parameters corresponding to the rule
        parameters. The following custom rules are handled:

        - `patch`: a patch index to be selected. If `patch` has a '+' or '-'
            suffix, increment the current patch index instead.
        - `lcdwrite`: a string to be written to the LCD, right-justified. If `format`
            is provided, the formatted `val` parameter is appended
        - `setpin`: the *index* of the pin in PIN_OUT to set using `val`. If the LED
            is set, set the state of the button toggle to match
        """
        if sig.type != 'clock':
            print(f"{sig}")
        if sig.type == 'cc':
            if sig.par1 == 0:
                self.load_bank(Path(f"bank{sig.par2}.yaml"))
                message = f"BK {sig.par2}\n"
                ser.write(message.encode('utf-8'))
            if sig.par1 == 15:
                #self.load_bank(Path(f"bank{sig.par2}.yaml"))
                #message = f"Bank {sig.par2}\n"
                #ser.write(message.encode('utf-8'))
                pno = sig.par2
                if pno < 0:
                    self.pno = (pno + sig.val) % len(fp.patches)
                elif pno < len(fp.patches):
                    self.pno = pno
                else:
                    sb.nokia_print(f"No pno {pno}!")
            if sig.par1 == 20:
                self.load_bank(Path(f"bank0.yaml"))
                ser.write(b'BK 0\n')
            if sig.par1 == 21:
                self.load_bank(Path(f"bank1.yaml"))
                ser.write(b'BK 1\n')
            if sig.par1 == 22:
                self.load_bank(Path(f"bank2.yaml"))
                ser.write(b'BK 2\n')
        if sig.type == 'prog':
            pno = sig.par1
            if pno < 0:
                self.pno = (pno + sig.val) % len(fp.patches)
            elif pno < len(fp.patches):
                self.pno = pno
            else:
                sb.nokia_print(f"No pno {pno}!")
        elif 'val' in sig:
            if 'patch' in sig:
                if sig.patch < 0:
                    self.pno = (self.pno + sig.val) % len(fp.patches)
                else:
                    self.pno = sig.patch
            elif 'lcdwrite' in sig:
                if 'format' in sig:
                    val = format(sig.val, sig.format)
                    self.lcdwrite = f"{sig.lcdwrite} {val}"[:COLS].rjust(COLS)
                else:
                    self.lcdwrite = sig.lcdwrite[-COLS:].rjust(COLS)
            elif 'setpin' in sig:
                if PIN_OUT[sig.setpin] == PIN_LED:
                    self.buttonstate = 1 if sig.val else 0
                sb.gpio_set(PIN_OUT[sig.setpin], sig.val)
        else:
            self.lastsig = sig

    def patchmode(self):
        """Selects a patch and displays the main screen"""
        if fp.patches:
            warn = fp.apply_patch(self.pno)
        else:
            warn = fp.apply_patch('')
        pno = self.pno
        while True:
            if fp.patches:
                sb.lcd_write(fp.patches[self.pno], 0, mode='scroll')
                message = f"PN {fp.patches[self.pno]}\n"
                ser.write(message.encode('utf-8'))
                if warn:
                    sb.lcd_write('; '.join(warn), 1, mode='scroll')
                    sb.waitfortap()
                sb.lcd_write(f"patch: {self.pno + 1}/{len(fp.patches)}", 1, mode='rjust')
                message = f"pno {self.pno + 1}\n"
                ser.write(message.encode('utf-8'))
            else:
                sb.lcd_write("No patches", 0, mode='ljust')
                if warn:
                    sb.lcd_write('; '.join(warn), 1, mode='scroll')
                    sb.waitfortap()
                sb.lcd_write("patch 0/0", 1, mode='rjust')
                message = f"pno {0}\n"
                ser.write(message.encode('utf-8'))
            #sb.lcd_write(sb.wificon, 1, 0)
            warn = []
            self.lastsig = None
            self.lcdwrite = None
            while True:
                if pno != self.pno:
                    return
                if self.lastsig:
                    #sb.lcd_blink(MIDIACT, 1, 1)
                    self.lastsig = None
                if self.lcdwrite:
                    #sb.lcd_blink('')
                    #sb.lcd_blink(self.lcdwrite, 1, delay=MENU_TIMEOUT)
                    self.lcdwrite = None
                event = sb.update()
                if event == NULL:
                    continue
                if event == INC and fp.patches:
                    self.pno = (self.pno + 1) % len(fp.patches)
                    return
                elif event == DEC and fp.patches:
                    self.pno = (self.pno - 1) % len(fp.patches)
                    return

    def load_bank(self, bank=""):
        """Bank loading menu"""
        lastbank = fp.currentbank
        lastpatch = fp.patches[self.pno] if fp.patches else ""
        if bank == "":
            last = str(fp.bankdir / fp.currentbank) if fp.currentbank else ""
            bankdir = Path(fp.bankdir)
            yaml_files = sorted(glob.glob(str(bankdir / "*.yaml")))
            _idx = 0
            if last != "":
                last_idx = yaml_files.index(last)
                if len(yaml_files) > (last_idx+1):
                    _idx = last_idx+1
            bank = Path(yaml_files[_idx])
            #bank = Path(Path(next_bank_path).name)
            #if bank == "": return False
        sb.lcd_write(bank.name, 0, mode='scroll', now=True)
        sb.lcd_write("loading patches ", 1, mode='ljust', now=True)
        sb.progresswheel_start()
        try: fp.load_bank(bank)
        except Exception as e:
            #sb.progresswheel_stop()
            sb.nokia_print("bank load error")
            return False
        #sb.progresswheel_stop()
        fp.write_config()
        self.connect_controls()
        if fp.currentbank != lastbank:
            self.pno = 0
        else:
            if lastpatch in fp.patches:
                self.pno = fp.patches.index(lastpatch)
            elif self.pno >= len(fp.patches):
                self.pno = 0
        return True


    def effects_menu(self):
        """FluidSynth effects setting menu"""
        i=0
        fxmenu_info = (
            # Name             fluidsetting              min    max   inc   format
            ('Reverb Size',   'synth.reverb.room-size',  0.0,   1.0,  0.1, '4.1f'),
            ('Reverb Damp',   'synth.reverb.damp',       0.0,   1.0,  0.1, '4.1f'),
            ('Rev. Width',    'synth.reverb.width',      0.0, 100.0,  0.5, '5.1f'),
            ('Rev. Level',    'synth.reverb.level',     0.00,  1.00, 0.01, '5.2f'),
            ('Chorus Voices', 'synth.chorus.nr',           0,    99,    1, '2d'),
            ('Chor. Level',   'synth.chorus.level',      0.0,  10.0,  0.1, '4.1f'),
            ('Chor. Speed',   'synth.chorus.speed',      0.1,  21.0,  0.1, '4.1f'),
            ('Chorus Depth',  'synth.chorus.depth',      0.3,   5.0,  0.1, '3.1f'),
            ('Gain',          'synth.gain',              0.0,   5.0,  0.1, '11.1f'))
        vals = [fp.fluidsetting_get(info[1]) for info in fxmenu_info]
        fxopts = [fxmenu_info[i][0] + ':' + format(vals[i], fxmenu_info[i][5]) for i in range(len(fxmenu_info))]
        while True:
            sb.lcd_write("Effects:", 0, mode='ljust')
            i = sb.choose_opt(fxopts, 1, i)
            if i < 0:
                break
            sb.lcd_write(fxopts[i], 0, mode='ljust')
            newval = sb.choose_val(vals[i], *fxmenu_info[i][2:], func=lambda x: fp.fluidsetting_set(fxmenu_info[i][1], x))
            if newval != None:
                fp.fluidsetting_set(fxmenu_info[i][1], newval, patch=self.pno)
                vals[i] = newval
                fxopts[i] = fxmenu_info[i][0] + ':' + format(newval, fxmenu_info[i][5])
            else:
                fp.fluidsetting_set(fxmenu_info[i][1], vals[i])

    def connect_controls(self):
        CHAN = 2
        TYPE = 'cc'             # 'cc' or 'note'
        DEC_PATCH = 21          # decrement the patch number
        INC_PATCH = 22          # increment the patch number
        BANK_INC = 0           # load the next bank

        # a continuous controller e.g. knob/slider can be used to select patches by value
        SELECT_PATCH = 5

        fp.add_router_rule(type=TYPE, chan=CHAN, par1=DEC_PATCH, par2='1-127', patch='1-')
        fp.add_router_rule(type=TYPE, chan=CHAN, par1=INC_PATCH, par2='1-127', patch='1+')
        fp.add_router_rule(type=TYPE, chan=CHAN, par1=BANK_INC, par2='1-127', bank=1)
        fp.add_router_rule(type=TYPE, chan=1,    par1=BANK_INC, par2='1-127', bank=1)
        if SELECT_PATCH != None:
            selectspec =  f"0-127=0-{min(len(fp.patches) - 1, 127)}" # transform CC values into patch numbers
            fp.add_router_rule(type='cc', chan=CHAN, par1=SELECT_PATCH, par2=selectspec, patch='select')
        #if SHUTDOWN_BTN != None:
            #fp.add_router_rule(type=TYPE, chan=CHAN, par1=SHUTDOWN_BTN, shutdown=1)
        #else:
            #fp.add_router_rule(type=TYPE, chan=CHAN, par1=DEC_PATCH, shutdown=1)
            #fp.add_router_rule(type=TYPE, chan=CHAN, par1=INC_PATCH, shutdown=1)

    def midi_devices(self):
        """Menu for connecting MIDI devices and monitoring"""
        sb.lcd_write("MIDI Devices:", 0, mode='ljust')
        readable = re.findall(" (\d+): '([^\n]*)'", sb.shell_cmd("aconnect -i"))
        rports, rnames = list(zip(*readable))
        p = sb.choose_opt([*rnames, "MIDI monitor.."], row=1, mode='scroll', timeout=-1)
        if p < 0: return
        if 0 <= p < len(rports):
            sb.lcd_write("Connect to:", 0, mode='ljust')
            writable = re.findall(" (\d+): '([^\n]*)'", sb.shell_cmd("aconnect -o"))
            wports, wnames = list(zip(*writable))
            op = sb.choose_opt(wnames, row=1, mode='scroll', timeout=-1)
            if op < 0: return
            if 'midiconnections' not in fp.cfg: fp.cfg['midiconnections'] = []
            fp.cfg['midiconnections'].append({rnames[p]: re.sub('(FLUID Synth) \(.*', '\\1', wnames[op])})
            fp.write_config()
            try: sb.shell_cmd(f"aconnect {rports[p]} {wports[op]}")
            except subprocess.CalledProcessError: pass
        elif p == len(rports):
            sb.lcd_clear()
            sb.lcd_write("MIDI monitor:", 0, mode='ljust')
            msg = self.lastsig
            while not sb.waitfortap(0.1):
                if self.lastsig == msg or self.lastsig == None: continue
                msg = self.lastsig
                if msg.type not in ('note', 'noteoff', 'cc', 'kpress', 'prog', 'pbend', 'cpress'): continue
                t = ('note', 'noteoff', 'cc', 'kpress', 'prog', 'pbend', 'cpress').index(msg.type)
                x = ("note", "noff", "  cc", "keyp", " prog", "pbend", "press")[t]
                if t < 4:
                    sb.lcd_write(f"ch{msg.chan:<3}{x}{msg.par1:3}={msg.par2:<3}", 1)
                else:
                    sb.lcd_write(f"ch{msg.chan:<3}{x}={msg.par1:<5}", 1)

    @staticmethod
    def midi_connect():
        """Make MIDI connections as enumerated in config"""
        devs = {client: port for port, client in re.findall(" (\d+): '([^\n]*)'", sb.shell_cmd("aconnect -io"))}
        for link in fp.cfg.get('midiconnections', []):
            mfrom, mto = list(link.items())[0]
            for client in devs:
                if re.search(mfrom.split(':')[0], client):
                    mfrom = re.sub(mfrom.split(':')[0], devs[client], mfrom, count=1)
                if re.search(mto.split(':')[0], client):
                    mto = re.sub(mto.split(':')[0], devs[client], mto, count=1)
            try: sb.shell_cmd(f"aconnect {mfrom} {mto}")
            except subprocess.CalledProcessError: pass 

    @staticmethod
    def usb_filecopy():
        """Menu for bulk copying files to/from USB drive"""
        sb.lcd_clear()
        sb.lcd_write("USB File Copy:", 0, mode='ljust')
        usb = re.search('/dev/sd[a-z]\d*', sb.shell_cmd("sudo blkid"))
        if not usb:
            sb.lcd_write("USB not found", 1, mode='ljust')
            sb.waitfortap(2)
            return
        opts = ['USB -> SquishBox', 'SquishBox -> USB', 'Sync with USB']
        j = sb.choose_opt(opts, row=1)
        if j < 0: return
        sb.lcd_write(opts[j], row=0, mode='ljust')
        sb.lcd_write("copying files ", 1, mode='rjust', now=True)
        sb.progresswheel_start()
        try:
            sb.shell_cmd("sudo mkdir -p /mnt/usbdrv")
            sb.shell_cmd(f"sudo mount -o owner,fmask=0000,dmask=0000 {usb[0]} /mnt/usbdrv/")
            if j == 0:
                sb.shell_cmd("rsync -rtL /mnt/usbdrv/SquishBox/ SquishBox/")
            elif j == 1:
                sb.shell_cmd("rsync -rtL SquishBox/ /mnt/usbdrv/SquishBox/")
            elif j == 2:
                sb.shell_cmd("rsync -rtLu /mnt/usbdrv/SquishBox/ SquishBox/")
                sb.shell_cmd("rsync -rtLu SquishBox/ /mnt/usbdrv/SquishBox/")
            sb.shell_cmd("sudo umount /mnt/usbdrv")
        except Exception as e:
            sb.progresswheel_stop()
            sb.display_error(e, "halted - errors: ")
        else:
            sb.progresswheel_stop()


if __name__ == "__main__":

    import os

    from fluidpatcher import FluidPatcher
    
    os.umask(0o002)
    sb = SquishBox()
    sb.lcd_clear()
    try: fp = FluidPatcher("SquishBox/squishboxconf.yaml")
    except Exception as e:
        sb.display_error(e, "bad config file: ")
    else:
        mainapp = FluidBox()
        mainapp.patchmode()
