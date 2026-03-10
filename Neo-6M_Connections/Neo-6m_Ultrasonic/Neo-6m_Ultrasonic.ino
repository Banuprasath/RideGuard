#include <TinyGPS++.h>
#include <SoftwareSerial.h>

TinyGPSPlus gps;
SoftwareSerial gpsSerial(2, 3);

#define TRIG_PIN 9
#define ECHO_PIN 10

long duration;
int distance;

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.println("System Ready: Ultrasonic + GPS");
}

void loop() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration != 0) {
    distance = duration * 0.034;
    Serial.print("DIST:");
    Serial.println(distance);
  }
  
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  
  if (gps.location.isUpdated()) {
    Serial.print("GPS:");
    Serial.print(gps.location.lat(), 6);
    Serial.print(",");
    Serial.print(gps.location.lng(), 6);
    Serial.print(",");
    Serial.print(gps.satellites.value());
    Serial.print(",");
    Serial.println(gps.speed.kmph());
  }
  
  delay(500);
}






// #include <TinyGPS++.h>
// #include <SoftwareSerial.h>

// TinyGPSPlus gps;
// SoftwareSerial gpsSerial(2,3);

// void setup()
// {
//   Serial.begin(9600);
//   gpsSerial.begin(9600);
// }

// void loop()
// {
//   while (gpsSerial.available())
//   {
//     gps.encode(gpsSerial.read());
//   }

//   if (gps.location.isUpdated())
//   {
//     Serial.println("------ GPS STATUS ------");

//     Serial.print("Latitude: ");
//     Serial.println(gps.location.lat(),6);

//     Serial.print("Longitude: ");
//     Serial.println(gps.location.lng(),6);

//     Serial.print("Satellites: ");
//     Serial.println(gps.satellites.value());

//     Serial.print("HDOP (Accuracy): ");
//     Serial.println(gps.hdop.value());

//     Serial.print("Fix Valid: ");
//     Serial.println(gps.location.isValid());

//     Serial.println("------------------------");
//     Serial.println();
//   }
// }