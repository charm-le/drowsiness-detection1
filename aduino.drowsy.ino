#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

const int buzzerPin = 8;
const int greenLedPin = 6; 
const int redLedPin = 7;   

bool isDrowsyMode = false;
unsigned long lastBuzzerTime = 0;
bool buzzerState = false;

void setup() {
  Serial.begin(9600);
  pinMode(buzzerPin, OUTPUT);
  pinMode(greenLedPin, OUTPUT);
  pinMode(redLedPin, OUTPUT);
  
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Drowsy Monitor");
  lcd.setCursor(0, 1);
  lcd.print("Status: Normal");

  digitalWrite(greenLedPin, HIGH);
  digitalWrite(redLedPin, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    
    if (data.startsWith("CLOSED")) {
      isDrowsyMode = true;
      
      // 데이터 파싱 (CLOSED,카운트,분)
      int firstComma = data.indexOf(',');
      int secondComma = data.indexOf(',', firstComma + 1);
      if (firstComma > 0 && secondComma > 0) {
        String countStr = data.substring(firstComma + 1, secondComma);
        String minStr = data.substring(secondComma + 1);
        
        // LCD 갱신
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Count: ");
        lcd.print(countStr);
        lcd.print(" Sleep!");
        
        lcd.setCursor(0, 1);
        lcd.print("Total Time: ");
        lcd.print(minStr);
        lcd.print("m");
      }
      
      // 빨간불 켜기
      digitalWrite(greenLedPin, LOW);
      digitalWrite(redLedPin, HIGH);
      
    } else if (data.startsWith("OPEN")) {
      isDrowsyMode = false;
      
      // 부저 끄기 및 초록불 켜기
      digitalWrite(buzzerPin, LOW);
      digitalWrite(redLedPin, LOW);
      digitalWrite(greenLedPin, HIGH);
      
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Drowsy Monitor");
      lcd.setCursor(0, 1);
      lcd.print("Status: Normal");
    }
  }

  // 졸음 상태일 때 삐-삐-삐 반복 경고음 출력 (딜레이 블로킹 방지)
 if (isDrowsyMode) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastBuzzerTime >= 300) { // 0.3초 간격
      lastBuzzerTime = currentMillis;
      buzzerState = !buzzerState;
      
      if (buzzerState) {
        tone(buzzerPin, 2000); // 2000Hz 주파수로 쩌렁쩌렁하게 울림 (소리가 더 큼)
      } else {
        noTone(buzzerPin); // 소리 끔
      }
    }
  } else {
    noTone(buzzerPin); // 평상시 확실하게 끔
  }
}