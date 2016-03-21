from flask import Flask, jsonify
import sys
import time
import serial
from threading import Thread
import re

app = Flask(__name__)

## Based on http://gejanssen.com/howto/Slimme-meter-uitlezen/
## First, run pip install pyserial Flask
## Also, I had to chmod /dev/ttyUSB0


# COM port config
# Baud rate might have to be set to 9600 for other meters
ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.SEVENBITS
ser.parity=serial.PARITY_EVEN
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port="/dev/ttyUSB0"


current = 0
current_return = 0
history = [0] * 20

last = []
def read_meter():
    global history
    global current
    global current_return

    current_pattern = re.compile('1-0:1.7.0\(([0-9]+\.[0-9]+)\*')
    current_return_pattern = re.compile('1-0:2.7.0\(([0-9]+\.[0-9]+)\*')
    ser.open()
    empty_first = False;
    while True:
        try:
            p1_raw = ser.readline()
        except:
            print("Problem reading serial port. Backing off for 60 seconds..")
            time.sleep(60)
            try:
                ser.close()
                ser.open()
                return
            except:
                pass

        current_line = str(p1_raw)

        match = current_pattern.match(current_line)
        if(match and match.group(1)):
            current = int(float(match.group(1)) * 1000)
            history = history[1:]
            history.append(current)
        else:
            ## Teruggegeven waarde zal vaak 0 zijn - deze wordt al ingehouden op de afgenomen stroom
            match = current_return_pattern.match(current_line)
            if match and match.group(1):
                current_return = int(float(match.group(1)) * 1000)

        if current_line[:1] == "!":
            empty_first = True
        elif empty_first:
                last[:] = []
                empty_first = False

        last.append(current_line)

    ## Unreacheable, but for future reference: close the serial connection here
    try:
        ser.close()
    except:
        pass

@app.route('/')
def show_current():
    return jsonify({"current_usage_mw":current,"current_return_mw":current_return, "history_usage_mw":history })

@app.route('/raw')
def show_raw():
    return ''.join(last)


thread = Thread(target = read_meter)
thread.daemon=True
thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=82)
