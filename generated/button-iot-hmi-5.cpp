#include <Homie.h>
### This is generated code ###

AsyncMqttClient& mqttClient = Homie.getMqttClient();
Bounce  debouncer  = Bounce();

const int PIN_BUTTON = 14;

void loopHandler() {
    //Serial.print("...");
    if (debouncer.update())
    {
    if ( digitalRead ( debouncer.read() ) == LOW ){
    //if ( digitalRead ( PIN_BUTTON ) == LOW ){
      Serial.print("/2");
      Serial.print("1");
      mqttClient.publish("/2", 1, true, "1");
    }
    }
}

void setup() {
  Serial.begin(115200);
  Homie.setResetTrigger(16, LOW, 2000); // reset pin, use before Homie.setup()
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  //digitalRead(PIN_BUTTON, HIGH);

  //String a = "foo";//Homie.getConfiguration().deviceId;
  //String b = String(Homie.getConfiguration().name);
  //uses macro expansion
  debouncer.attach( PIN_BUTTON );
  debouncer.interval(30);

  Homie_setFirmware("bare-minimum", "1.0.0"); // The "_" is not a typo! See Magic bytes
  Homie.setLoopFunction(loopHandler);
  Homie.setup();
}

void loop() {
  Homie.loop();
}



