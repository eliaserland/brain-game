import pyfirmata
import time

class Labyrinth():

	def __init__(self, usb_port):
		#Establishes the connection between the Arduino and the python scripts. 
		#It also sets the start angles for the servos.
		#Inner servo should be servo 1, ie pin 5
		#Outer servo should be servo 2, ie pin 6
		self.Angle_Left_1 = 80
		self.Angle_Right_1 = 120
		
		self.Angle_Left_2 = 120
		self.Angle_Right_2 = 75
		
		self.usb_port = usb_port        
		print("in __init__")
		self.board = pyfirmata.Arduino(self.usb_port)

		self.board.servo_config(5)
		self.servo1 = self.board.get_pin('d:5:s')
		self.servo1.write(self.Angle_Left_1)

		self.board.servo_config(6)
		self.servo2 = self.board.get_pin('d:6:s')
		self.servo2.write(self.Angle_Left_2)
		print('Done initializing arduinos')
	def __del__(self):
		#Returns the servos to start position when object is removed or script terminated
		print("Shutting down program, returning to start position")
		self.turn_left(1)
		self.turn_left(2)
		print("Shutting down program")

		self.board.exit()
#Function that turns the servos to the right postion.
#Takes the inputs 1 or 2 depending on which servo is wanted 

	def turn_right(self,servomotor):

		startpos =int(self.servo1.read())
		#print(startpos)
		if servomotor == 1:
			startpos=int(self.servo1.read())
			#print('right1')
			for i in range(startpos,self.Angle_Right_1,+1):
				self.servo1.write(i)
				#time.sleep(0.05)
				self.board.pass_time(0.05)
				#print(self.servo1.read())
		if servomotor == 2:

			startpos =int(self.servo2.read())
			for i in range(startpos,self.Angle_Right_2,-1):
				self.servo2.write(i)
				self.board.pass_time(0.05)
				#time.sleep(0.5)
				#print(self.servo2.read())            

			#print('right2')

	#Function that turns the servos to the left position.
	#Takes the inputs 1 or 2 depending on which servo is wanted 
	def turn_left(self,servomotor):

		if servomotor == 1:
			startpos =int(self.servo1.read())
			for i in range(startpos,self.Angle_Left_1,-1):
				self.servo1.write(i)
				self.board.pass_time(0.05)
				#time.sleep(0.1)
				#print(self.servo1.read())            

			#print('left1')
		if servomotor == 2:

			startpos =int(self.servo2.read())
			for i in range(startpos,self.Angle_Left_2,+1):
				self.servo2.write(i)
				self.board.pass_time(0.05)
				#time.sleep(0.5)
				#print(self.servo2.read())                

			#print('left2')
