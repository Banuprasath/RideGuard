// #include "soc/soc.h"
// #include "soc/rtc_cntl_reg.h"

// #include "esp_camera.h"
// #include "FS.h"
// #include "SD_MMC.h"

// // ===== AI THINKER ESP32-CAM PINS =====
// #define PWDN_GPIO_NUM     32
// #define RESET_GPIO_NUM    -1

// #define XCLK_GPIO_NUM      0
// #define SIOD_GPIO_NUM     26
// #define SIOC_GPIO_NUM     27
// #define Y9_GPIO_NUM       35
// #define Y8_GPIO_NUM       34
// #define Y7_GPIO_NUM       39
// #define Y6_GPIO_NUM       36
// #define Y5_GPIO_NUM       21
// #define Y4_GPIO_NUM       19
// #define Y3_GPIO_NUM       18
// #define Y2_GPIO_NUM        5
// #define VSYNC_GPIO_NUM    25
// #define HREF_GPIO_NUM     23
// #define PCLK_GPIO_NUM     22
// // ====================================

// #define ACK_LED 4

// // ---------- LED ACK (safe pulse) ----------
// void ackBlink(int times = 1) {
//   for (int i = 0; i < times; i++) {
//     digitalWrite(ACK_LED, HIGH);
//     delay(80);
//     digitalWrite(ACK_LED, LOW);
//     delay(120);
//   }
// }

// // ---------- Create event folder (timestamp-based) ----------
// String createEventFolder() {
//   if (!SD_MMC.exists("/ACCIDENT")) {
//     SD_MMC.mkdir("/ACCIDENT");
//     delay(100);
//   }

//   String folder = "/ACCIDENT/event_" + String(millis());
//   SD_MMC.mkdir(folder.c_str());
//   delay(100);

//   return folder;
// }

// // ---------- Write log inside event folder ----------
// void writeEventLog(String folder) {
//   File f = SD_MMC.open(folder + "/log.txt", FILE_WRITE);
//   if (f) {
//     f.println("Event: Accident Capture");
//     f.println("Timestamp (ms): " + String(millis()));
//     f.println("Images: 5");
//     f.println("Status: Completed");
//     f.close();
//   }
// }

// // ---------- Capture images ----------
// void captureAccidentImages() {
//   String eventFolder = createEventFolder();

//   for (int i = 1; i <= 5; i++) {
//     camera_fb_t *fb = esp_camera_fb_get();
//     if (!fb) continue;

//     String imgPath = eventFolder + "/img_" + String(i) + ".jpg";
//     File file = SD_MMC.open(imgPath, FILE_WRITE);

//     if (file) {
//       file.write(fb->buf, fb->len);
//       file.close();
//     }

//     esp_camera_fb_return(fb);
//     delay(700);
//   }

//   writeEventLog(eventFolder);
// }

// // ======================= SETUP =======================
// void setup() {
//   WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);  // disable brownout

//   pinMode(ACK_LED, OUTPUT);
//   digitalWrite(ACK_LED, LOW);

//   Serial.begin(115200);
//   delay(3000);

//   camera_config_t config;
//   config.ledc_channel = LEDC_CHANNEL_0;
//   config.ledc_timer   = LEDC_TIMER_0;
//   config.pin_d0       = Y2_GPIO_NUM;
//   config.pin_d1       = Y3_GPIO_NUM;
//   config.pin_d2       = Y4_GPIO_NUM;
//   config.pin_d3       = Y5_GPIO_NUM;
//   config.pin_d4       = Y6_GPIO_NUM;
//   config.pin_d5       = Y7_GPIO_NUM;
//   config.pin_d6       = Y8_GPIO_NUM;
//   config.pin_d7       = Y9_GPIO_NUM;
//   config.pin_xclk     = XCLK_GPIO_NUM;
//   config.pin_pclk     = PCLK_GPIO_NUM;
//   config.pin_vsync    = VSYNC_GPIO_NUM;
//   config.pin_href     = HREF_GPIO_NUM;
//   config.pin_sccb_sda = SIOD_GPIO_NUM;
//   config.pin_sccb_scl = SIOC_GPIO_NUM;
//   config.pin_pwdn     = PWDN_GPIO_NUM;
//   config.pin_reset    = RESET_GPIO_NUM;

//   config.xclk_freq_hz = 20000000;
//   config.pixel_format = PIXFORMAT_JPEG;
//   config.frame_size   = FRAMESIZE_QVGA;
//   config.jpeg_quality = 12;
//   config.fb_count     = 1;

//   esp_camera_init(&config);
//   SD_MMC.begin();

//   Serial.println("ESP32-CAM READY");
// }

// // ======================= LOOP =======================
// void loop() {
//   if (Serial.available()) {
//     String cmd = Serial.readString();
//     cmd.trim();

//     if (cmd == "CAPTURE") {
//       ackBlink(2);            // command received
//       captureAccidentImages();
//       ackBlink(1);            // capture completed
//     }
//   }
// }





#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"
#include "FS.h"
#include "SD_MMC.h"

// ================= CAMERA PINS (AI THINKER) =================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22
// ============================================================

#define ACK_LED 4

// 🔴 CHANGE WIFI DETAILS
const char* ssid = "banu-prasath";
const char* password = "banu-prasath";

WebServer server(80);

// ================= LED ACK =================
void ackBlink(int times = 1) {
  for (int i = 0; i < times; i++) {
    digitalWrite(ACK_LED, HIGH);
    delay(80);
    digitalWrite(ACK_LED, LOW);
    delay(120);
  }
}

// ================= CREATE EVENT FOLDER =================
String createEventFolder() {
  if (!SD_MMC.exists("/ACCIDENT")) {
    SD_MMC.mkdir("/ACCIDENT");
    delay(100);
  }

  String folder = "/ACCIDENT/event_" + String(millis());
  SD_MMC.mkdir(folder.c_str());
  delay(100);

  return folder;
}

// ================= WRITE LOG =================
void writeEventLog(String folder) {
  File f = SD_MMC.open(folder + "/log.txt", FILE_WRITE);
  if (f) {
    f.println("Event: Accident Capture");
    f.println("Timestamp(ms): " + String(millis()));
    f.println("Images: 5");
    f.println("Status: Completed");
    f.close();
  }
}

// ================= CAPTURE IMAGES =================
void captureAccidentImages() {
  String eventFolder = createEventFolder();

  for (int i = 1; i <= 5; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) continue;

    String imgPath = eventFolder + "/img_" + String(i) + ".jpg";
    File file = SD_MMC.open(imgPath, FILE_WRITE);

    if (file) {
      file.write(fb->buf, fb->len);
      file.close();
    }

    esp_camera_fb_return(fb);
    delay(700);
  }

  writeEventLog(eventFolder);
}

// ================= HTTP: SERVE IMAGE =================
void handleImage() {
  if (!server.hasArg("file")) {
    server.send(400, "text/plain", "Missing file argument");
    return;
  }

  String path = server.arg("file");
  File file = SD_MMC.open(path);

  if (!file) {
    server.send(404, "text/plain", "File not found");
    return;
  }

  server.streamFile(file, "image/jpeg");
  file.close();
}

// ================= HTTP: LATEST EVENT =================
void handleLatestEvent() {
  File root = SD_MMC.open("/ACCIDENT");
  File dir = root.openNextFile();
  String latest = "";

  while (dir) {
    if (dir.isDirectory() && String(dir.name()).startsWith("event_")) {
      latest = dir.name();
    }
    dir = root.openNextFile();
  }

  if (latest == "") {
    server.send(404, "text/plain", "No events");
    return;
  }

  server.send(200, "text/plain", latest);
}

// ================= SETUP =================
void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);  // 🔥 prevent reset

  pinMode(ACK_LED, OUTPUT);
  digitalWrite(ACK_LED, LOW);

  Serial.begin(115200);
  delay(3000);

  // ---- Camera config ----
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_camera_init(&config);
  SD_MMC.begin();

  // ---- Wi-Fi ----
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  Serial.print("🌐 ESP32-CAM IP: ");
  Serial.println(WiFi.localIP());

  // ---- HTTP Routes ----
  server.on("/image", handleImage);
  server.on("/latest", handleLatestEvent);
  server.begin();

  Serial.println("ESP32-CAM READY");
}

// ================= LOOP =================
void loop() {
  server.handleClient();

  if (Serial.available()) {
    String cmd = Serial.readString();
    cmd.trim();

    if (cmd == "CAPTURE") {
      ackBlink(2);
      captureAccidentImages();
      ackBlink(1);
    }
  }
}
