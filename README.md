# Object Classification for Vehicle

這個專案收集了車輛使用的物件辨識程式與周邊韌體，包含以 OpenCV 進行色球偵測的 Python 程式，以及控制車體伺服馬達與 Wi-Fi 的 ESP8266 範例。

## 專案結構

- `ball_detection/`：使用 Flask 與 OpenCV 偵測紅、黃、藍色球並估計其距離與方向。
- `car_motor and camera/`：ESP8266 的馬達與相機伺服控制程式。
- `carservo/`：ESP8266 建立 Wi-Fi 存取點或透過 Web 伺服器控制伺服馬達的範例。

## Ball Detection

`ball_detection` 目錄提供一個 Flask 與 OpenCV 的應用程式。

### 安裝環境

使用 `pip`：

```bash
pip install -r ball_detection/requirements.txt
```

或使用 `poetry`：

```bash
cd ball_detection
poetry install --no-root
```

### 環境設定

依照 `ball_detection/.env.example` 建立 `.env`，`hfov.py` 可協助計算相機的水平視角。

### 執行方式

```bash
python ball_detection/main.py
```

## 韌體程式

- `car_motor and camera`：示範伺服馬達掃描與基本馬達控制。
- `carservo/WiFiAccessPoint_8266`：建立 Wi-Fi 存取點。
- `carservo/WiFiManualWebServer_esp8266_servo`：透過網址指令控制兩顆伺服馬達。

可使用 Arduino IDE 或其他相容的工具鏈開啟並燒錄這些程式至 ESP8266。

