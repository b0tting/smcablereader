#!/usr/bin/python
from flask import Flask, jsonify
import sys
import time
import serial
from threading import Thread
import re
import logging

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

## Size of the history list
history_size = 20

current = 0
current_return = 0
history = [0] * history_size
last_frame = None

def get_mw_from_w(w):
    return int(float(w) * 1000)

def read_meter():
    """
    Read the state that the smart meter pushes out and set the result in global vars
    """
    global history
    global last_frame
    global current
    global current_return

    current_pattern = re.compile('1-0:1.7.0\(([0-9]+\.[0-9]+)\*')
    current_return_pattern = re.compile('1-0:2.7.0\(([0-9]+\.[0-9]+)\*')

    ## Open serial connection.
    ## If this fails, try getting "cu -l /dev/ttyUSB0 -s 115200 --parity=none" to work first
    ser.open()


    ## So we will continously attempt to read data from the socket, automatically pausing
    ## if there is none.
    current_frame = [];
    while True:
        try:
            current_line = str(ser.readline())

        except:
            log.error("Problem reading serial port. Backing off for 60 seconds..")
            time.sleep(60)
            try:
                ## We failed? Restart, then rerun the loop
                ser.close()
                ser.open()
                return
            except:
                pass

        current_frame.append(current_line)

        ## If we reach the last line in the message, starting with the ! terminator, get the
        ## mw's and reset our line reader.
        if current_line[:1] == "!":
            try:
                ## Match the current line with the pattern for energy use
                ## Not the most efficient method, since we only need the first hit but the list will still be fully
                ## rolled through the matcher. 
                current = [get_mw_from_w(m.group(1)) for line in current_frame for m in [current_pattern.search(line)] if m][0]

                ## Match the current line with the pattern for energy use
                current_return = [get_mw_from_w(m.group(1)) for line in current_frame for m in [current_return_pattern.search(line)] if m][0]

                history.append(current - current_return)
                history = history[-history_size:]
            except IndexError, e:
                log.error("Could not find the current mWh, but did connect. This could be due to starting halfway through a frame, in that case this error will not appear again.")

            ## clone the current frame for use in the /raw method, then empty the current frame for the next run
            last_frame = list(current_frame)
            current_frame[:] = []


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
    return ''.join(last_frame)

## Kick off the meter thread so that it runs seperate from the webserver
thread = Thread(target = read_meter)
thread.daemon=True
thread.start()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=82)
