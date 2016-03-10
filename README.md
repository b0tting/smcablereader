# SMCableReader

A gloriously simple Python script that serves your current energy consumption in JSON. Based on the information found on http://gejanssen.com/howto/Slimme-meter-uitlezen. Succesfully tested on a Landis meter.  

## Installation
This script boots a Flask webserver on port 80. Requirements are thus Flask and a library for reading a serial port. 
- pip install pyserial Flask

I had some minor issues with reading from the /dev/ttyUSB0 by default, solved by a "chmod a+rw /dev/ttyUSB0" 