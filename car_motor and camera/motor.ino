#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi 配置信息
const char* ssid = "***";       // 替換為你的WiFi名稱
const char* password = "***";   // 替換為你的WiFi密碼

// 伺服器地址
const char* serverURL = "http://------/data"; // 替換為你的伺服器地址

// 馬達引腳定義
#define PIN_IN1  13  // GPIO13
#define PIN_IN2  12  // GPIO12
#define PIN_ENA  14  // GPIO14 (PWM 支援)

#define PIN_IN3  4  // GPIO4
#define PIN_IN4  5  // GPIO5
#define PIN_ENB  0  // GPIO0 (PWM 支援)

// 初始值
char turnDirection[10] = "";  // 預設方向為 ""
float moveTime[10];      // 預設時間

void setup() {
  // 初始化串口
  Serial.begin(115200);

  // 初始化馬達引腳
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_IN3, OUTPUT);
  pinMode(PIN_IN4, OUTPUT);
  pinMode(PIN_ENB, OUTPUT);

  // 連接Wi-Fi
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
}

void forward(int straight_duration) {
  digitalWrite(PIN_IN1, HIGH); // A 馬達正轉
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);  // B 馬達正轉
  digitalWrite(PIN_IN4, HIGH);

  for (int speed = 0; speed <= 1023; speed += 10) {  // 調整速度 (ESP8266 PWM 範圍 0-1023)
    analogWrite(PIN_ENA, speed);
    analogWrite(PIN_ENB, speed);
    delay(10);
  }

  delay(straight_duration);  // 持續運行

  for (int speed = 1023; speed >= 0; speed -= 10) {
    analogWrite(PIN_ENA, speed);
    analogWrite(PIN_ENB, speed);
    delay(10);
  }
}

void fetchDataFromServer() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client; // 創建 WiFiClient 實例
    HTTPClient http;

    http.begin(client, serverURL); // 使用新的 API
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      String response = http.getString();
      StaticJsonDocument<128> doc;
      DeserializationError error = deserializeJson(doc, response);

      if (!error) {
//        JsonArray move_time = doc["move_time"];
        const float move_time1 = doc["move_time1"];
        const float move_time2 = doc["move_time2"];
        const char* direction = doc["turn_direction"];
        Serial.println(move_time1);
        Serial.println(move_time2);

//        // 更新全局變數
//        for (size_t i = 0; i < move_time.size(); i++) {
////          moveTime[i] = move_time[i].as<float>();
//            moveTime[i] = float(move_time[i]);
//        }
        moveTime[0] = move_time1;
        moveTime[1] = move_time2;
        strncpy(turnDirection, direction, sizeof(turnDirection));

        // 打印接收到的數據
        Serial.print("Move Time: [");
        for (size_t i = 0; i < 2; i++) {
          Serial.print(moveTime[i]);
          if (i < 2 - 1) Serial.print(", ");
        }
        Serial.println("]");
        Serial.print("Turn Direction: ");
        Serial.println(turnDirection);
      } else {
        Serial.print("JSON parsing failed: ");
        Serial.println(error.c_str());
      }
    } else {
      Serial.print("HTTP GET failed, error: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

void loop() {
  fetchDataFromServer();  // 從伺服器獲取數據

  forward(moveTime[0]*1000);   // 執行前進

  if (strcmp(turnDirection, "Right") == 0) {
    // 執行右轉的代碼
  } else if (strcmp(turnDirection, "Left") == 0) {
    // 執行左轉的代碼
  }

  delay(10000);  // 每 10 秒執行一次循環
}
