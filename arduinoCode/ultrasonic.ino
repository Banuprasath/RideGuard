#define TRIG_PIN 9
#define ECHO_PIN 10

long duration;
int distance;

void setup() {

  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void loop() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return;

  distance = duration * 0.034 ;

  Serial.print("DIST:");
  Serial.println(distance);

  delay(500);
}


















// #define TRIG_PIN 9
// #define ECHO_PIN 10

// long duration;
// float distance;

// void setup() {
//   Serial.begin(9600);
//   pinMode(TRIG_PIN, OUTPUT);
//   pinMode(ECHO_PIN, INPUT);
// }

// void loop() {
//   digitalWrite(TRIG_PIN, LOW);
//   delayMicroseconds(2);
//   digitalWrite(TRIG_PIN, HIGH);
//   delayMicroseconds(10);
//   digitalWrite(TRIG_PIN, LOW);

//   duration = pulseIn(ECHO_PIN, HIGH, 60000);

//   if (duration == 0) {
//     Serial.println("No echo");
//     delay(300);
//     return;
//   }

//   distance = duration * 0.0343 ;// / 2.0;

//   Serial.print("Distance: ");
//   Serial.print(distance);
//   Serial.println(" cm");

//   delay(300);
// }
