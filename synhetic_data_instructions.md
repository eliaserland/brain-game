# Generera och ta emot syntetiskt data OpenBCI GUI -> python

## Generera syntetiskt data i OpenBCI GUI:

 - Kör din OpenBCI GUI executable.
 - Data Source: SYNTHETIC (Algorithmic)
 - Channel count: 8 chan
 - Start session.
 - Start data source.
 - Välj widget "Networking".
 - Protocol: "Serial"
 - Data type: "TimeSeries"
 - Baud/Port: "57600" and \[name of port\], i mitt fall "/dev/ttyS0"
 - Start Serial stream.
	
## Ta emot synetiskt data i python:

 - kör testscriptet: `python3 test.py --board-id -1 --serial-port [name of port]`
 - i mitt fall: `python3 test.py --board-id -1 --serial-port /dev/ttyS0`
 
Board-ID:
 - `board-id=-1`: syntetiskt board
 - `board-id=0` : cyton board
