/**
 * @file	ArduinoRemoteDebug.h
 * @author	Looi Kian Seong
 * @date	10-9-2020
 * @brief	A class for ESP8266 to perform remote debug printing 
 *			from a connected Arduino Uno
 *
 */
 
#ifndef	ArduinoRemoteDebug_H
#define	ArduinoRemoteDebug_H

#ifndef	EXTRA_FUNC_CALL_FLAG
	#define	EXTRA_FUNC_CALL_FLAG
#endif

#ifndef DEVICEID
	#define DEVICEID	Unknown
#endif

#include <AbstractPubSub.h>

#define	CMD_DEBUG_START				0x44		// 'D'
#define CMD_DEBUG_STOP				0x45		// 'E'
#define	CMD_RESET_DEVICE			0x52		// 'R'
#define CMD_PING_DEVICE				0x50		// 'P'
#define MAX_TIMEOUT					1000UL
#define MIN(A, B)					(A) < (B)? (A):(B)

class ArduinoRemoteDebug: virtual public AbstractPubSub {
	public: 
		ArduinoRemoteDebug(WiFiClient *wifi_client, uint8_t reset_pin, int8_t ind_LED=-1): AbstractPubSub(wifi_client, reset_pin, ind_LED), PubSubClient(*wifi_client) {
//			_setMQTTCallback();
			_appLoop = ([this] () { this->_debugLoop(); });
		}
		void setReadTimeout(uint32_t timeout);
	
	protected:
		uint32_t _timeout;
		bool _is_debugging = false;
		
		void _debugLoop();
		void _callback(char *topic, byte *payload, uint32_t length);
		void _resetDevice();
		void _startDebugging();
		void _stopDebugging();
};

#endif		/* ArduinoRemoteDebug_H */

