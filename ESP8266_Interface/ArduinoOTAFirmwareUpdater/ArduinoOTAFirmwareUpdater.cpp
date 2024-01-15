/**
 * @file	ArduinoOTAFirmwareUpdater.cpp
 * @author	Looi Kian Seong
 * @date	10-9-2020
 * @brief	A class for ESP8266 to perform OTA firmware update 
 *			on a connected Arduino Uno
 *
 */

#include "ArduinoOTAFirmwareUpdater.h"

bool ArduinoOTAFirmwareUpdater::_waitOptibootRes_1s() {
	_start_time = millis();
	while((Serial.available() < 2) && !(_is_timeout = ((millis() - _start_time) > TIMEOUT)));
	if(_is_timeout || (Serial.read() != 0x14) || (Serial.read() != 0x10)) {
		publish(_tx_topic, WARNING_STK_FAILED);
		return false;
	}
	
	return true;
}

void ArduinoOTAFirmwareUpdater::_getSync() {
	Serial.write(0x30);
	Serial.write(0x20);
	if(_waitOptibootRes_1s()) {
		publish(_tx_topic, OK);
		_is_flashing = true;
		_start_time = millis();
	} else {
		_is_flashing = false;
	}
}

bool ArduinoOTAFirmwareUpdater::_sendHex(const uint8_t *hex, uint16_t len) {		// STK500 Protocol
	Serial.write(0x55);
	Serial.write(_addr & 0xFF);
	Serial.write(_addr >> 8);
	Serial.write(0x20);
	_hex_size -= len;
	
	if(_waitOptibootRes_1s()) {
		Serial.write(0x64);
		Serial.write((uint8_t)((len >> 8) & 0xFF));
		Serial.write((uint8_t)(len & 0xFF));
		Serial.write(0x46);
		
		for(uint8_t i=0;i<len;i++) {
			Serial.write(*(hex + i));
		}
		
		Serial.write(0x20);
//		_hex_size -= len;
	} else {
		publish(_tx_topic, FLASH_FAILED);
		publish(_tx_topic, "END");
		return false;
	}
	
	if(_waitOptibootRes_1s()) {
		if(_hex_size) {
			_addr += (len >> 1);
			publish(_tx_topic, OK);
		} else {
			Serial.write(0x51);
			Serial.write(0x20);
			publish(_tx_topic, "Done flashing!");
			_waitOptibootRes_1s();
			publish(_tx_topic, "Exiting bootloader...");
			publish(_tx_topic, "END");
			return false;
		}
	} else {
		publish(_tx_topic, FLASH_FAILED);
		publish(_tx_topic, "END");
		return false;
	}
	
	return true;
}

void ArduinoOTAFirmwareUpdater::_startFlashing(byte *payload, uint32_t length) {
	_hex_size = 0;
	
	for(uint8_t i=1;i<length;i++) {
		uint8_t payload_i = (uint8_t)payload[i];
		
		if((payload_i >= '0') && (payload_i <= '9')) {
			_hex_size *= 10;
			_hex_size += payload_i - '0';
		} else {
			publish(_tx_topic, "[FAILED] Invalid hex length payload received.");
			publish(_tx_topic, "END");
			return;
		}
	}
	
	_hex_size_copy = _hex_size;
	_addr = 0;
	digitalWrite(_reset_pin, LOW);
	_flushRxBuff();
	char msg[128];
	sprintf(msg, "[STATUS] Connected Device: %s\n\t\t ESP Programmer Serial Baudrate: %d", _client_id, _baudrate);
	publish(_tx_topic, msg);
	delay(200);
	digitalWrite(_reset_pin, HIGH);
	delay(300);
	_getSync();
}

void ArduinoOTAFirmwareUpdater::_setStartFlashTimeout() {
	if(_hex_size == _hex_size_copy) {
		if(_is_flashing && ((millis() - _start_time) > TIMEOUT)) {
			_is_flashing = false;
		}
	}
}

void ArduinoOTAFirmwareUpdater::_callback(char *topic, byte *payload, uint32_t length) {
	if(_is_flashing) {
		_is_flashing = _sendHex((uint8_t *)payload, (uint16_t)length);
	} else {
		byte cmd = payload[0];
		if(cmd == CMD_FLASH_START) {
			_startFlashing(payload, length);
		} else if(cmd == CMD_UPDATE_BAUDRATE) {
			_setBaudrate(payload, length);
		}
	}
}

