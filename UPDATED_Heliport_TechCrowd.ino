#include <EEPROM.h>

int analogPin = 0;
int raw = 0;
int Vin = 5;
float Vout = 0;
float R1 = 168000;
float R2 = 0;
float buffer = 0;
float level=0;
int buttonPin = 12;
int buttonState = 0; 
int outputToRasp = 8;
int LEDcalib = 10;
float forLevel;
float newLevel;
bool tmp = false;
bool isCalling = false;
unsigned long int incrementToCalibrate;


void setup(){
Serial.begin(9600);
pinMode(LEDcalib, OUTPUT);
pinMode(buttonPin, INPUT_PULLUP);
pinMode(outputToRasp, OUTPUT);
getNewLevel();
Serial.println("**********SETUP*************");
//newLevel = (EEPROM_read(0) * 10);
Serial.println(newLevel);
Serial.println("***********END SETUP************");
}

void loop(){
  
  raw = analogRead(analogPin);
  if(raw){
    buffer = raw * Vin;
    Vout = (buffer)/1024.0;
    buffer = (Vin/Vout) - 1;
    R2= R1 * buffer;

    Serial.println("***********************");
    Serial.println("newLevel is: ");
    Serial.println(newLevel);
    Serial.println("***********************");
    
    if (R2 > newLevel){
      if (R2 > 500000){
        Serial.println("ERROR ");
        Serial.println("Possible problems:");
        Serial.println("walkie-talkie a.k.a radio is out of the power");
        Serial.println(R2);
        digitalWrite(LEDcalib, HIGH);
        delay(250);
        digitalWrite(LEDcalib, LOW);
        isCalling = true;
      }
      else {
        digitalWrite(LED_BUILTIN, HIGH);
        Serial.println("HIGH  ");
        digitalWrite(LEDcalib, HIGH);
        Serial.println(R2);
        digitalWrite(outputToRasp, LOW);
        isCalling = true;
      }
    }
    else {
        digitalWrite(LED_BUILTIN, LOW);
        Serial.println("LOW  ");        
        digitalWrite(LEDcalib, LOW);
        Serial.println(R2);
        digitalWrite(outputToRasp, HIGH);
        isCalling = false;
      }
  buttonState = digitalRead(buttonPin);
  if (buttonState == HIGH || tmp == true){
    tmp = true;
    if (buttonState == LOW)
    {
    Serial.println("calibration........");
    digitalWrite(LEDcalib, HIGH);
    getNewLevel();
    digitalWrite(LEDcalib, LOW);
    tmp = false;
    }
   }
   incrementToCalibrate += 1;
   Serial.println("incrementToCalibrate");
   Serial.println(incrementToCalibrate);
   if(isCalling == false){
       if ((incrementToCalibrate > 120) ){
          Serial.println("##################CALL CALIBRATION FUNCTION BY TIME####################");
          getNewLevel();
          incrementToCalibrate = 0;
      }
   }
  delay(500);
  
  }
  else
  {
    Serial.println("*************NO VALUE FROM PHOTORESISTOR************");
    Serial.println("Possible problems:");
    Serial.println("photoresistor is unplugged");
    isCalling = true;
  }
}
float getNewLevel() {
  Serial.println("calibration STARTED");
  float R2_1 = 0;
  float forLevel = 0;
    for (int i = 0; i < 20; i++)
    {
       raw = analogRead(analogPin);
        if(raw){
          buffer = raw * Vin;
          Vout = (buffer)/1024.0;
          buffer = (Vin/Vout) - 1;
          R2_1= R1 * buffer;
          forLevel += R2_1;
          Serial.print("-----------------iteration  ");
          Serial.println(i);
          }
    }    
    newLevel = (forLevel/20)+900; 
    Serial.println("calibration ENDED");
    Serial.println("new level is: ");
    Serial.println(newLevel);
    Serial.println("______________________________________________________________________________");
    Serial.println("WRITING LEVEL TO EEPROM - please be careful(max. 100 000 Write/Read action!)");
    word newLevelModified = (newLevel/10); // max value of word is 2^16 = 65536 -> our newLevel is in range {10000;20000}, so I divided this value by 10 because of limitation of WORD and usage of the larger variables occupies a lot of space in our small EEPROM memory   
    Serial.println("our new modified value to EEPROM");
    Serial.println(newLevelModified);
//    EEPROM_write(0, newLevelModified);
} 

//void EEPROM_write(uint8_t a, word b){
//    Serial.println("eeprom write was called!!!!!!!!!!!");
//  
//        EEPROM.write(a, lowByte(b));
//        EEPROM.write(a + 1, highByte(b));
//    
//}
//
//float EEPROM_read(uint8_t a)
//{
//    Serial.print("read level value from EEPROM: ");
//    Serial.print(a+1);
//    Serial.println(a);
//    Serial.println("<<<<<<<<<<<<<<<<<<END READ EEPROM>>>>>>>>>>>>>>>>>>>");
//    return word(EEPROM.read(a + 1), EEPROM.read(a));
//}
