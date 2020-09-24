/**
 * @file	AbstractPubSub.h
 * @author	Looi Kian Seong
 * @date	10-9-2020
 * @brief	Abstract class which defines some common methods 
 *			which will be derived by the child class
 *
 */
 
#ifndef	AbstractPubSub_H
#define	AbstractPubSub_H

#ifndef DEVICEID
	#define DEVICEID	Unknown
#endif

#define CREATE_TOPIC(X, Y)      STR(X)STR(/)STR(Y)
#define HELPER_STR(X)          	#X
#define STR(X)         			HELPER_STR(X)

#define	DEFAULT_BAUDRATE		115200UL
#define	CMD_UPDATE_BAUDRATE		0x55	// 'U'
#define	DEVICE_ONLINE			"Online"
#define	DEVICE_OFFLINE			"Offline"
#define	WILL_TOPIC				STR(DEVICEID)"/device_status"

#include <Arduino.h>
#include <PubSubClient.h>
#include <ESP8266WiFi.h>
#include <functional>

class AbstractPubSub: virtual public PubSubClient {
	public: 
		AbstractPubSub(WiFiClient *wifi_client, uint8_t reset_pin, int8_t ind_LED=-1): PubSubClient(*wifi_client) {
			_client_id = STR(DEVICEID);
			_reset_pin = reset_pin;
			_ind_LED = ind_LED;
			
			_setBaudrate(DEFAULT_BAUDRATE);
			Serial.begin(_baudrate);
			pinMode(_reset_pin, OUTPUT);
			digitalWrite(_reset_pin, HIGH);
			
			if(_ind_LED > -1) {
				pinMode(_ind_LED, OUTPUT);
				digitalWrite(_ind_LED, LOW);
			}
		}
		
		void clientLoop() {
			if(!connected()) {
				if(_ind_LED > -1)
					digitalWrite(_ind_LED, LOW);
					_reconnect();
			} else {
				loop();
			#ifdef	EXTRA_FUNC_CALL_FLAG
				_appLoop();
			#endif
			}
		}

		void setUsername(const char *username) { _username = username; }
		void setPassword(const char *password) { _password = password; }
		void setTxTopic(const char *tx_topic) { _tx_topic = tx_topic; }
		void setRxTopic(const char *rx_topic) { _rx_topic = rx_topic; }
		void setMQTTCallback() { setCallback([this] (char *topic, byte *payload, unsigned int length) { this->_callback(topic, payload, length); }); }

	protected:
		const char *_client_id;
		const char *_username;
		const char *_password;
		const char *_tx_topic;
		const char *_rx_topic;
		uint32_t _baudrate;
		uint8_t _reset_pin;
		int8_t _ind_LED;
		
	#ifdef	EXTRA_FUNC_CALL_FLAG
		std::function<void()> _appLoop;
	#endif

		void _flushRxBuff() { while(Serial.available()) Serial.read(); }
		
		void _setBaudrate(uint32_t baudrate) {
			_baudrate = baudrate;
			Serial.flush();
			Serial.updateBaudRate(_baudrate);
		}
		
		void _setBaudrate(byte *payload, uint32_t length) {
			uint32_t baudrate = 0;
			for(uint8_t i=1;i<length;i++) {
				uint8_t payload_i = (uint8_t)payload[i];
				
				if((payload_i >= '0') && (payload_i <= '9')) {
					baudrate *= 10;
					baudrate += payload_i - '0';
				} else {
					baudrate = _baudrate;
					break;
				}
			}
			
			_setBaudrate(baudrate? baudrate:_baudrate);
		}
		
		void _reconnect() {
			if (connect(_client_id, _username, _password, WILL_TOPIC, 0, true, DEVICE_OFFLINE)) {
				digitalWrite(_ind_LED, HIGH);
				publish(WILL_TOPIC, DEVICE_ONLINE, true);
				subscribe(_rx_topic);
			}
		}
		
		virtual void _callback(char* topic, byte* payload, unsigned int length) = 0;
};

#endif		/* AbstractPubSub_H */

