import pyfirmata
import time

class LabyrintStyrning(object):
    theta1 = 90.0;
    theta2 = 90.0;


    board = None
    servo1 = None
    servo2 = None



    def __init__(self):
        theta1 = 90.0;
        theta2 = 90.0;
        print("in __init__")
        self.board = pyfirmata.Arduino('/dev/cu.usbmodem14101')

        self.board.servo_config(5, angle = self.theta1)
        self.servo1 = self.board.get_pin('d:5:s')
        self.servo1.write(self.theta1)

        self.board.servo_config(6, angle = self.theta2)
        self.servo2 = self.board.get_pin('d:6:s')
        self.servo2.write(self.theta2)
        print('Done')
    #def __del__(self):
    #    print("Shutting down program")
    #    self.goto(90, 90)
    #    self.board.exit()

    def turn_right(self,servomotor):
        VinkelHoger = 70
        startpos =int(self.servo1.read())
        #print(startpos)
        if servomotor == 1:
            startpos=int(self.servo1.read())
            #print('right1')
            for i in range(startpos,VinkelHoger,-1):
                self.servo1.write(i)
                #time.sleep(0.05)
                self.board.pass_time(0.07)
                print(self.servo1.read())
        if servomotor == 2:
            startpos =int(self.servo2.read())
            for i in range(startpos,VinkelHoger,-1):
                self.servo2.write(i)
                self.board.pass_time(0.07)
                print(self.servo2.read())

            #print('right2')


    def turn_left(self,servomotor):
        VinkelVanster = 110
        if servomotor == 1:
            startpos =int(self.servo1.read())
            for i in range(startpos,VinkelVanster,+1):
                self.servo1.write(i)
                #time.sleep(0.05)
                self.board.pass_time(0.07)
                print(self.servo1.read())

            #print('left1')
        if servomotor == 2:
            startpos =int(self.servo2.read())
            for i in range(startpos,VinkelVanster,+1):
                self.servo2.write(i)
                self.board.pass_time(0.07)
                print(self.servo2.read())

            #print('left2')
