# SMCableReader

A gloriously simple Python script that serves your current energy consumption in JSON. Based on the information found on http://gejanssen.com/howto/Slimme-meter-uitlezen. Succesfully tested on a Landis meter.  

## Installation
This script boots a Flask webserver on port 80. Requirements are thus Flask and a library for reading a serial port. 
- pip install pyserial Flask

I had some minor issues with reading from the /dev/ttyUSB0 by default, solved by a "chmod a+rw /dev/ttyUSB0"

## Usage
Start. Then either open 0.0.0.0:82 for a JSON view of the current usage and last 10 measurements. Or open /raw to see the last full output. Note that this terminates with a !, so if the last line does not start with an exclamation mark your meter was still busy writing it's output when you requested the page. 



 