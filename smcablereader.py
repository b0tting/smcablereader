#!/usr/bin/python
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
    """
    Read the state that the smart meter pushes out and set the result in global vars
    """
    global history
    global current
    global current_return

    current_pattern = re.compile('1-0:1.7.0\(([0-9]+\.[0-9]+)\*')
    current_return_pattern = re.compile('1-0:2.7.0\(([0-9]+\.[0-9]+)\*')

    ## Open serial connection.
    ## If this fails, try getting "cu -l /dev/ttyUSB0 -s 115200 --parity=none" to work first
    ser.open()
    empty_first = False;

    ## So we will continously attempt to read data from the socket, automatically pausing
    ## if there is none.
    while True:
        try:
            p1_raw = ser.readline()
        except:
            print("Problem reading serial port. Backing off for 60 seconds..")
            time.sleep(60)
            try:
                ## We failed? Restart, then rerun the loop
                ser.close()
                ser.open()
                return
            except:
                pass

        current_line = str(p1_raw)

        ## Match the current line with the pattern for energy use
        match = current_pattern.match(current_line)
        if(match and match.group(1)):
            current = int(float(match.group(1)) * 1000)
            history = history[1:]
            history.append(current)
        ## Match the current line with the pattern for energy return to the supplier
        else:
            ## Often, this will be zero even with your solar panels blazing. This is because the meter already
            ## substracts electricity delivered from current energy consumed
            match = current_return_pattern.match(current_line)
            if match and match.group(1):
                current_return = int(float(match.group(1)) * 1000)

        ## If we reach the last line in the message, starting with the ! terminator, reset our
        ## line reader.
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
    ## Just dump the contents of the list of raw messages
    return ''.join(last)

## Kick off the meter thread so that it runs seperate from the webserver
thread = Thread(target = read_meter)
thread.daemon=True
thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=82)
