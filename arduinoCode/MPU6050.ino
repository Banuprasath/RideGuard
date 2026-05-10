#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

int16_t ax, ay, az;

// Baseline values
long base_ax = 0;
const int CALIBRATION_SAMPLES = 20;

// Thresholds (tune if needed)
const int LEFT_THRESHOLD  = -6000;
const int RIGHT_THRESHOLD =  6000;

// Simple stability counter
int stableCount = 0;
const int STABLE_LIMIT = 3;

void setup() {
  Serial.begin(9600);
  delay(1000);

  Wire.begin(D2, D1);
  Wire.setClock(100000);

  Serial.println("Initializing MPU6050...");
  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("MPU6050 connection FAILED");
    return;
  }

  Serial.println("Calibrating baseline...");
  calibrateBaseline();
  Serial.println("Calibration done");
}

void calibrateBaseline() {
  long sum = 0;

  for (int i = 0; i < CALIBRATION_SAMPLES; i++) {
    mpu.getAcceleration(&ax, &ay, &az);
    sum += ax;
    delay(50);
  }

  base_ax = sum / CALIBRATION_SAMPLES;
}

void loop() {
  mpu.getAcceleration(&ax, &ay, &az);

  int delta_ax = ax - base_ax;

  String state = "NONE";

  if (delta_ax < LEFT_THRESHOLD) {
    stableCount++;
    if (stableCount >= STABLE_LIMIT) {
      state = "LEFT";
    }
  }
  else if (delta_ax > RIGHT_THRESHOLD) {
    stableCount++;
    if (stableCount >= STABLE_LIMIT) {
      state = "RIGHT";
    }
  }
  else {
    stableCount = 0;
  }

  Serial.print("FALL:");
  Serial.println(state);

  delay(500);   // Safe delay for ESP8266
}
