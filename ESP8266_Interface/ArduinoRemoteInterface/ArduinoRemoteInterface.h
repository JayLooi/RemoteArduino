/**
 * @file	ArduinoRemoteInterface.h
 * @author	Looi Kian Seong
 * @date	10-9-2020
 * @brief	A class for ESP8266 to perform remote debug printing from and 
 *			OTA firmware update on a connected Arduino Uno
 *
 */
 
#ifndef	ArduinoRemoteInterface_H
#define	ArduinoRemoteInterface_H

#ifndef DEVICEID
	#define DEVICEID	Unknown
#endif

#include <ArduinoOTAFirmwareUpdater.h>
#include <ArduinoRemoteDebug.h>

class ArduinoRemoteInterface: public ArduinoOTAFirmwareUpdater, public ArduinoRemoteDebug {
	public: 
		ArduinoRemoteInterface(WiFiClient *wifi_client, uint8_t reset_pin, int8_t ind_LED=-1)
			:	PubSubClient(*wifi_client), 
				AbstractPubSub(wifi_client, reset_pin, ind_LED), 
				ArduinoOTAFirmwareUpdater(wifi_client, reset_pin, ind_LED), 
				ArduinoRemoteDebug(wifi_client, reset_pin, ind_LED) {
			
			_appLoop = ([this] () { this->_setStartFlashTimeout(); this->_debugLoop(); }); 
//			_setMQTTCallback();
		}
	
	private:
		void _callback(char *topic, byte *payload, uint32_t length) {
			if(_is_flashing) {
				_is_flashing = _sendHex((uint8_t *)payload, (uint8_t)length);
			} else {
				byte cmd = payload[0];
				switch(cmd) {
					case CMD_FLASH_START:
						_startFlashing(payload, length);
						if(_is_flashing) {
							_is_debugging = false;
						}
						break;
					
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
		}
};

#endif		/* ArduinoRemoteInterface_H */

