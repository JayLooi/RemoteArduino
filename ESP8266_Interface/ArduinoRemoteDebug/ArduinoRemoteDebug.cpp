/**
 * @file	ArduinoRemoteDebug.cpp
 * @author	Looi Kian Seong
 * @date	10-9-2020
 * @brief	A class for ESP8266 to perform remote debug printing 
 *			from a connected Arduino Uno
 *
 */

#include "ArduinoRemoteDebug.h"

void ArduinoRemoteDebug::setReadTimeout(uint32_t timeout) {
	_timeout = MIN(timeout, MAX_TIMEOUT);
}

void ArduinoRemoteDebug::_debugLoop() {
	if(_is_debugging) {
		char debug_log[128];
		memset(debug_log, 0, 128);
		uint8_t n = 0;
		uint32_t start_time = millis();
		while(((millis() - start_time) < _timeout) && (n < 127)) {
			if(Serial.available()) {
				debug_log[n++] = (char)Serial.read();
				start_time = millis();
			}
		}
		
		if(n > 0) {
			publish(_tx_topic, debug_log);
		}
	}
}

void ArduinoRemoteDebug::_callback(char *topic, byte *payload, uint32_t length) {
	byte cmd = payload[0];
	switch(cmd) {
		case CMD_RESET_DEVICE:
			_resetDevice();
			break;
		
		case CMD_DEBUG_START:
			_startDebugging();
			break;
		
		case CMD_DEBUG_STOP:
			_stopDebugging();
			break;
		
		case CMD_UPDATE_BAUDRATE:
			_setBaudrate(payload, length);
			break;
	}
}

void ArduinoRemoteDebug::_resetDevice() {
	digitalWrite(_reset_pin, LOW);
	_flushRxBuff();
	delay(200);
	digitalWrite(_reset_pin, HIGH);
}

void ArduinoRemoteDebug::_startDebugging() {
	_is_debugging = true;
}

void ArduinoRemoteDebug::_stopDebugging() {
	_is_debugging = false;
}

