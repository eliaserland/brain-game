#-*- coding: latin-1 -*-
import serial
import time

arduino = serial.Serial('COM3', 9600, timeout = 1) #Creates arduino object
time.sleep(3)

while True:
    command = input("Servo position: ")
    #print(bytes(command, "latin-1"))
    arduino.write(bytes(command, 'latin-1')) #sends command to arduino via serial port
    
    value = arduino.readlines() #reads all lines sent from arduino via Serial.print()
    for line in value:
        print(line)
        
    if command == 'q':
        exit()