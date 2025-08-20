#include <ESP8266WiFi.h>

// 定義伺服馬達的控制腳位
int servoPin = 14; // D5 on NodeMCU

// WiFi 資訊
const char *ssid = "***";
const char *password = "***";

void setup() {
 Serial.begin(115200);

 // WiFi 連接
 WiFi.begin(ssid, password);
 while (WiFi.status() != WL_CONNECTED) {
   delay(1000);
   Serial.println("正在連接 Wi-Fi...");
 }
 Serial.println("Wi-Fi 已連接！");

 // 設定伺服馬達的腳位
  pinMode(servoPin, OUTPUT);
}

// 重新定義 map 函數以支援浮點數
double mapf(double x, double in_min, double in_max, double out_min, double out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// ServoWrite 函數：模擬 PWM 來控制伺服馬達
void ServoWrite(int servoPin, double degree, double delay_ms) {
  double dutyCycleMs = mapf(degree, -90.0, 90.0, 0.5, 2.5); // -90°到90°對應0.5ms到2.5ms
  for (int i = 0; i < delay_ms / 20; i++) { // sg90 需要 20ms 的週期
    digitalWrite(servoPin, HIGH);
    delayMicroseconds(dutyCycleMs * 1000); // 高電平時間
    digitalWrite(servoPin, LOW);
    delayMicroseconds((20 - dutyCycleMs) * 1000); // 低電平時間
  }
}

void loop() {
  // 從 -90° 平滑旋轉到 90°
  for (int angle = -90; angle <= 90; angle++) {
    ServoWrite(servoPin, angle, 5); // 每個角度花費 5ms
  }
  delay(1000);

  // 從 90° 平滑旋轉回 -90°
  for (int angle = 90; angle >= -90; angle--) {
    ServoWrite(servoPin, angle, 5); // 每個角度花費 5ms
  }
  delay(1000);
}
