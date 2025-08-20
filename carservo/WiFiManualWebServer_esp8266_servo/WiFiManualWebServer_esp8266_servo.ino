/*
    This sketch demonstrates how to set up a simple HTTP-like server.
    The server will set a GPIO pin depending on the request
      http://server_ip/gpio/0 will set the GPIO2 low,
      http://server_ip/gpio/1 will set the GPIO2 high
    server_ip is the IP address of the ESP8266 module, will be
    printed to Serial when the module is connected.
*/

#include <ESP8266WiFi.h>
#include <Servo.h>


#ifndef STASSID
#define STASSID "ESP32"               //*************************************
#define STAPSK "12345678"           //*************************************
#endif

const char* ssid = STASSID;
const char* password = STAPSK;

// Create an instance of the server
// specify the port to listen on as an argument
WiFiServer server(80);


Servo myservo_R;  // create servo object to control a servo // twelve servo objects can be created on most boards
Servo myservo_L;

void setup() {
  Serial.begin(115200);
  delay(500);
  // prepare LED
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, 0);

  myservo_R.attach(13);  // attaches the servo on GIO0 to the servo object
  myservo_L.attach(12);  // attaches the servo on GIO15 to the servo object
  
  // Connect to WiFi network
  Serial.println();
  Serial.println();
  Serial.print(F("Connecting to "));
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(F("."));
  }
  Serial.println();
  Serial.println(F("WiFi connected"));

  // Start the server
  server.begin();
  Serial.println(F("Server started"));

  // Print the IP address
  Serial.println(WiFi.localIP());
}

void loop() {
  // Check if a client has connected
  WiFiClient client = server.accept();
  if (!client) { return; }
  Serial.println(F("new client"));

  client.setTimeout(5000);  // default is 1000

  // Read the first line of the request
  String req = client.readStringUntil('\r');
  Serial.println(F("request: "));
  Serial.println(req);

  // Match the request
  int val;
  if (req.indexOf(F("/gpio/0")) != -1) {
      val = 0;
  } else if (req.indexOf(F("/gpio/1")) != -1) {
      val = 1;
  } else if (req.indexOf(F("/r")) != -1) {                                      //*************************************   
      myservo_R.write(0);  // tell servo to go to position in variable 'pos'    //*************************************
      delay(15);
      myservo_L.write(0);                                                       //*************************************
      delay(15);
  } else if (req.indexOf(F("/y")) != -1) {                                      //*************************************
      myservo_R.write(0);  // tell servo to go to position in variable 'pos'    //*************************************
      delay(15);
      myservo_L.write(180);                                                     //*************************************
      delay(15);
  } else if (req.indexOf(F("/g")) != -1) {                                       //************************************* 
      myservo_R.write(180);  // tell servo to go to position in variable 'pos'   //*************************************
      delay(15);
      myservo_L.write(180);                                                      //************************************* 
      delay(15);
  } 
  else  
  {
    Serial.println(F("invalid request"));
    val = digitalRead(LED_BUILTIN);
  }

  // Set LED according to the request
  digitalWrite(LED_BUILTIN, val);

  // read/ignore the rest of the request
  // do not client.flush(): it is for output only, see below
  while (client.available()) {
    // byte by byte is not very efficient
    client.read();
  }

  // Send the response to the client
  // it is OK for multiple small client.print/write,
  // because nagle algorithm will group them into one single packet
  client.print(F("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<!DOCTYPE HTML>\r\n<html>\r\nGPIO is now "));
  client.print((val) ? F("high") : F("low"));
  client.print(F("<br><br>Click <a href='http://"));
  client.print(WiFi.localIP());
  client.print(F("/gpio/1'>here</a> to switch LED GPIO on, or <a href='http://"));
  client.print(WiFi.localIP());
  client.print(F("/gpio/0'>here</a> to switch LED GPIO off.</html>"));

  client.print(F("/H"));

  // The client will actually be *flushed* then disconnected
  // when the function returns and 'client' object is destroyed (out-of-scope)
  // flush = ensure written data are received by the other side
  Serial.println(F("Disconnecting from client"));

  

  
}
