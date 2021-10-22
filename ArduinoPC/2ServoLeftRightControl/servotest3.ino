#include <Servo.h>
Servo myservo1; 
Servo myservo2;

String inChar; 
int pos1;
int pos2; 
int left = 45;
int right = 135; 
int neutral = 90;
void setup() {
 
  myservo1.attach(5);
  myservo2.attach(6);
  
  Serial.begin(9600);
  Serial.setTimeout(10);

  myservo1.write(neutral);
  myservo2.write(neutral);
  
}

void loop(){    

  
  if(Serial.available())   // if data available in serial port
    { 
    inChar = Serial.readString();
    
    if (inChar[0] == '1')
    {
      Serial.println("Control servo 1 ");
      Serial.println(inChar);
      //pos1 = inChar.substring(2).toInt();
      
      if (inChar[2] == 'l')
      {
        myservo1.write(left);
      }
      
      if (inChar[2] == 'r')
      {
        myservo1.write(right); 
      }

      if (inChar[2] == '0')
      {
        myservo1.write(neutral)
      }
    }

    if (inChar[0] == '2')
    {
      Serial.println("Control servo 2 ");
      Serial.println(inChar);
      //pos2 = inChar.substring(2).toInt();
      if (inChar[2] == 'l')
      {
        myservo2.write(left);
      }
      if (inChar[2] == 'r')
      {
        myservo2.write(right); 
      }

      if (inChar[2] == '0')
      {
        myservo2.write(neutral);
      }
    }




//    if (inChar[0] == '2')
//    {
//      Serial.print("Starts at 2 ");
//      Serial.print(inChar);
//      pos2 = inChar.substring(2).toInt();
//      myservo2.write(pos2);
//    }


//    pos1 = inChar.toInt();   // change datatype from string to integer        
//    myservo1.write(pos1);     // move servo
//    myservo2.write(pos2);
//    Serial.print("Servo is in position ");
//    Serial.print(inChar.substring(2));
    }

}
