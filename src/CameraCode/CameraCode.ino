#include <WiFi.h>
#include "esp_camera.h"
#include "esp_timer.h"
#include "img_converters.h"
#include "Arduino.h"
#include "fb_gfx.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "esp_http_server.h"          

#include "board_config.h"             

const char* ssid     = "Ximenes";
const char* password = "ximenes123";

#define LED_GPIO_NUM 4

#define LED_METAL 12
#define LED_PAPEL 13
#define LED_PLASTICO 14
#define LED_BIO 15

// MJPEG stream constants
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY     = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART         = "Content-Type: image/jpeg\r\nContent-Length: %u\r\nX-Timestamp: %d.%06d\r\n\r\n";

httpd_handle_t stream_httpd = NULL;

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char part_buf[128];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;

  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
      break;
    }

    if (fb->format != PIXFORMAT_JPEG) {
      bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
      esp_camera_fb_return(fb);
      fb = NULL;
      if (!jpeg_converted) {
        Serial.println("JPEG compression failed");
        res = ESP_FAIL;
        break;
      }
    } else {
      _jpg_buf_len = fb->len;
      _jpg_buf = fb->buf;
    }

    if (res == ESP_OK) {
      size_t hlen = snprintf(part_buf, sizeof(part_buf), _STREAM_PART, _jpg_buf_len,
                             fb->timestamp.tv_sec, fb->timestamp.tv_usec);
      res = httpd_resp_send_chunk(req, part_buf, hlen);
    }

    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }

    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
    }

    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if (_jpg_buf) {
      free(_jpg_buf);
      _jpg_buf = NULL;
    }

    if (res != ESP_OK) break;
  }
  return res;
}

static esp_err_t classe_handler(httpd_req_t *req) {

  char query[32];

  if (httpd_req_get_url_query_str(req, query, sizeof(query)) == ESP_OK) {

    char param[16];

    if (httpd_query_key_value(query, "valor", param, sizeof(param)) == ESP_OK) {

      int valor = atoi(param);

      Serial.print("Classe recebida: ");
      Serial.println(valor);

      digitalWrite(LED_METAL, LOW);
      digitalWrite(LED_PAPEL, LOW);
      digitalWrite(LED_PLASTICO, LOW);
      digitalWrite(LED_BIO, LOW);

      switch (valor) {
        case 0: digitalWrite(LED_METAL, HIGH); break;
        case 1: digitalWrite(LED_PAPEL, HIGH); break;
        case 2: digitalWrite(LED_PLASTICO, HIGH); break;
        case 3: digitalWrite(LED_BIO, HIGH); break;
        default: Serial.println("Valor invalido"); break;
      }
    }
  }

  httpd_resp_send(req, "OK", HTTPD_RESP_USE_STRLEN);
  return ESP_OK;
}

void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  httpd_uri_t classe_uri = {
    .uri       = "/classe",
    .method    = HTTP_GET,
    .handler   = classe_handler,
    .user_ctx  = NULL
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    httpd_register_uri_handler(stream_httpd, &classe_uri);
  } else {
    Serial.println("Erro ao iniciar servidor HTTP");
  }
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Configura pins dos LEDs como OUTPUT
  pinMode(LED_METAL, OUTPUT);
  pinMode(LED_PAPEL, OUTPUT);
  pinMode(LED_PLASTICO, OUTPUT);
  pinMode(LED_BIO, OUTPUT);

  // Apaga todos os LEDs inicialmente
  digitalWrite(LED_METAL, LOW);
  digitalWrite(LED_PAPEL, LOW);
  digitalWrite(LED_PLASTICO, LOW);
  digitalWrite(LED_BIO, LOW);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size   = FRAMESIZE_VGA;   // 640x480
    config.jpeg_quality = 10;
    config.fb_count     = 2;
  } else {
    config.frame_size   = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count     = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Init camera failed 0x%x\n", err);
    return;
  }

  pinMode(LED_GPIO_NUM, OUTPUT);
  digitalWrite(LED_GPIO_NUM, LOW);

  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi ");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_GPIO_NUM, !digitalRead(LED_GPIO_NUM));
  }
  Serial.println("\nWiFi conectado");
  Serial.print("IP: http://");
  Serial.println(WiFi.localIP());

  startCameraServer();

  Serial.print("Stream: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/stream");
}

void loop() {
  delay(10000);
  digitalWrite(LED_GPIO_NUM, HIGH);
  delay(1000);
  digitalWrite(LED_GPIO_NUM, LOW);
}