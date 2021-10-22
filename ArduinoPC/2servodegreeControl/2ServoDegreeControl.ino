#include <Servo.h>
Servo myservo1; 
Servo myservo2;

String inChar; 
int pos1;
int pos2; 
int l = 70;
int r = 110; 

void setup() {
 
  myservo1.attach(5);
  myservo2.attach(6);
  
  Serial.begin(9600);
  Serial.setTimeout(10);
}

void loop(){    
  myservo1.write(0)
  myservo2.write(0)
  
  if(Serial.available())   // if data available in serial port
    { 
    inChar = Serial.readString();

    if (inChar[0] == '1')
    {
      Serial.print("Control servo 1 ");
      Serial.print(inChar);
      pos1 = inChar.substring(2).toInt();
      myservo1.write(pos1);
    }

    if (inChar[0] == '2')
    {
      Serial.print("Starts at 2 ");
      Serial.print(inChar);
      pos2 = inChar.substring(2).toInt();
      myservo2.write(pos2);
    }


//    pos1 = inChar.toInt();   // change datatype from string to integer        
//    myservo1.write(pos1);     // move servo
//    myservo2.write(pos2);
//    Serial.print("Servo is in position ");
//    Serial.print(inChar.substring(2));
    }

}
