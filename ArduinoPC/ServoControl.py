# -*- coding: latin-1 -*-
import serial
import time

channel = 'COM3'

arduino = serial.Serial(channel, 9600, timeout=1)  # Creates arduino object
time.sleep(3)


def turn_left(servoNumber):
    toLeft = str(servoNumber) + ' l'
    arduino.write(bytes(toLeft, 'latin-1'))


def turn_right(servonumber):
    toRight = str(servonumber) + ' l'
    arduino.write(bytes(toRight, 'latin-1'))


while True:
    command = input("What servo and left or right (1/2 l/r: ")
    # print(bytes(command, "latin-1"))
    # sends command to arduino via serial port
    if command[0] == 1:
        if command[2] == 'l':
            turn_left(1)

        if command[2] == 'r':
            turn_right(1)

    if command[0] == 2:
        if command[2] == 'l':
            turn_left(2)

        if command[2] == 'r':
            turn_right(2)

    value = arduino.readlines()  # reads all lines sent from arduino via Serial.print()
    for line in value:
        print(line.decode(encoding='latin-1'))

    if command == 'q':
        break
