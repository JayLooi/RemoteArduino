/**
 * @file	ArduinoOTAFirmwareUpdater.h
 * @author	Looi Kian Seong
 * @date	10-9-2020
 * @brief	A class for ESP8266 to perform OTA firmware update 
 *			on a connected Arduino Uno
 *
 */
 
#ifndef	ArduinoOTAFirmwareUpdater_H
#define	ArduinoOTAFirmwareUpdater_H

#ifndef	EXTRA_FUNC_CALL_FLAG
	#define	EXTRA_FUNC_CALL_FLAG
#endif

#ifndef DEVICEID
	#define DEVICEID	Unknown
#endif

#include <AbstractPubSub.h>

#define CMD_FLASH_START			0x46		// 'F'
#define OK						"OK"
#define WARNING_STK_FAILED		"[WARNING] STK FAILED"
#define FLASH_FAILED			"[FAILED] FLASHING FAILED"
#define TIMEOUT					1000UL

class ArduinoOTAFirmwareUpdater: virtual public AbstractPubSub {
	public: 
		ArduinoOTAFirmwareUpdater(WiFiClient *wifi_client, uint8_t reset_pin, int8_t ind_LED=-1): AbstractPubSub(wifi_client, reset_pin, ind_LED), PubSubClient(*wifi_client) { 
//			_setMQTTCallback();
			_appLoop = ([this] () { this->_setStartFlashTimeout(); });
		}
	
	protected:
		uint16_t _addr;
		uint32_t _hex_size;
		uint32_t _hex_size_copy;
		bool _is_flashing = false;
		uint32_t _start_time;
		bool _is_timeout = false;
		
		void _startFlashing(byte *payload, uint32_t length);
		void _setStartFlashTimeout();
		void _callback(char *topic, byte *payload, uint32_t length);
		bool _waitOptibootRes_1s();
		void _getSync();
		bool _sendHex(const uint8_t *hex, uint16_t len);
};

#endif		/* ArduinoOTAFirmwareUpdater_H */

