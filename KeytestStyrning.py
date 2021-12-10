import pyfirmata
import time

class LabyrintStyrning(object):
    theta1 = 90.0; 
    theta2 = 90.0;

 
    board = None
    servo1 = None
    servo2 = None
  

#Function that establishes the connection between the Arduino
#and the python scripts. It also sets the start angles for the servos.

    def __init__(self):
        #Den inre ska vara servo 1 dvs pin 5
        #Den yttre ska vara servo 2 dvs pin 6
        self.VinkelVanster1 =75;
        self.VinkelVanster2 = 120;
        self.VinkelHoger1 = 110;
        self.VinkelHoger2 = 70;
        #theta1 = 90.0; 
        #theta2 = 90.0;        
        print("in __init__")
        self.board = pyfirmata.Arduino('COM3')

        self.board.servo_config(5, angle = self.theta1)
        self.servo1 = self.board.get_pin('d:5:s')
        self.servo1.write(self.VinkelVanster1)

        self.board.servo_config(6, angle = self.theta2)
        self.servo2 = self.board.get_pin('d:6:s')
        self.servo2.write(self.VinkelVanster2)
        print('Done')
    def __del__(self):
        
        print("Shutting down program")
        self.servo1.write(self.VinkelVanster1)
        self.servo2.write(self.VinkelVanster2)
        self.board.exit()
#Function that turns the servos to the right postion.
#Takes the inputs 1 or 2 depending on which servo is wanted 

    def turn_right(self,servomotor):
        
        startpos =int(self.servo1.read())
        print(startpos)
        if servomotor == 1:
            startpos=int(self.servo1.read())
            #print('right1')
            for i in range(startpos,self.VinkelHoger1,+1):
                self.servo1.write(i)
                #time.sleep(0.05)
                self.board.pass_time(0.05)
                print(self.servo1.read())
        if servomotor == 2:
            
            startpos =int(self.servo2.read())
            for i in range(startpos,self.VinkelHoger2,-1):
                self.servo2.write(i)
                self.board.pass_time(0.05)
                #time.sleep(0.5)
                print(self.servo2.read())            
            
            #print('right2')
     
    #Function that turns the servos to the left position.
    #Takes the inputs 1 or 2 depending on which servo is wanted 
    def turn_left(self,servomotor):
       
        if servomotor == 1:
            startpos =int(self.servo1.read())
            for i in range(startpos,self.VinkelVanster1,-1):
                self.servo1.write(i)
                self.board.pass_time(0.05)
                #time.sleep(0.1)
                print(self.servo1.read())            
            
            #print('left1')
        if servomotor == 2:
           
            startpos =int(self.servo2.read())
            for i in range(startpos,self.VinkelVanster2,+1):
                self.servo2.write(i)
                self.board.pass_time(0.05)
                #time.sleep(0.5)
                print(self.servo2.read())                
            
            #print('left2')
