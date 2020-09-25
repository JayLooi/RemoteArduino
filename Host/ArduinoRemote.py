import os
import paho.mqtt.client as mqtt
import struct
from time import time, sleep

HEX_BUFF_SIZE = 128


class ArduinoRemote:
    def __init__(self, hex_stream_fp, client_id, host, port, username, pw, tx_topic, rx_topic, status_topic, statusLog=print, deviceStatusLog=print, flashLog=print, debugLog=print, exceptionLog=print):
        self.n_of_bytes = 0
        self.sent_bytes = 0
        self.hex_stream_f = None
        self.hex_stream_fp = hex_stream_fp
        self.host = host
        self.port = port
        self.username = username
        self.pw = pw
        self.tx_topic = tx_topic
        self.rx_topic = rx_topic
        self.status_topic = status_topic
        self.is_flashing = False
        self.is_debugging = False
        self.statusLog = statusLog
        self.deviceStatusLog = deviceStatusLog
        self.flashLog = flashLog
        self.debugLog = debugLog
        self.exceptionLog = exceptionLog
        self.n_packet = 0
        self.is_connected = False
        self._start_time = 0

        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._onConnect
        self.client.on_disconnect = self._onDisconnect
        self.client.on_publish = self._onPublish
        self.client.on_message = self._onMessage
        self.client.on_subscribe = self._onSubscribe

    def _publish(self, payload):
        try:
            self.client.publish(topic=self.tx_topic, payload=payload)

        except ValueError as e:
            self.exceptionLog(e)

    def _subscribe(self):
        try:
            self.client.subscribe(topic=self.rx_topic)
            self.client.subscribe(topic=self.status_topic)

        except ValueError as e:
            self.exceptionLog(e)

    def _onConnect(self, client, userdata, flags, rc):
        if rc == 0:
            self._subscribe()
            self.is_connected = True
            self.statusLog('Connected')

        else:
            self.statusLog('Connect fail [%d]' % rc)

    def _onDisconnect(self, client, userdata, rc):
        self.is_connected = False
        self.is_flashing = False
        self.is_debugging = False
        self.resetOnMessageCallback()
        self.statusLog('Disconnected')
        self.deviceStatusLog('Unknown')
        if rc != 0:
            self.client.unsubscribe(self.rx_topic)
            self.client.unsubscribe(self.status_topic)

    def _onPublish(self, client, userdata, mid):
        pass

    def _onMessage(self, client, userdata, msg):
        if msg.topic == self.status_topic:
            self.deviceStatusLog(msg.payload.decode())

    def _onSubscribe(self, client, userdata, mid, granted_qos):
        pass

    def _onMessage_flashing(self, client, userdata, msg):
        if msg.topic == self.rx_topic:
            payload = msg.payload.decode()
            if payload == 'OK':
                hex_line = self.hex_stream_f.read(HEX_BUFF_SIZE)
                if hex_line:
                    self._publish(hex_line)
                    n = len(hex_line)
                    self.sent_bytes = self.sent_bytes + n
                    self.n_packet = self.n_packet + 1
                    self.flashLog('[INFO] Sending packet %d: %d bytes' % (self.n_packet, n))
                    self.is_flashing = True

            elif payload == 'END':
                self.is_flashing = False
                self.resetOnMessageCallback()

            else:
                self.flashLog('Device: ' + payload)

        else:
            self._onMessage(client, userdata, msg)

    def _onMessage_debugging(self, client, userdata, msg):
        if msg.topic == self.rx_topic:
            self.debugLog(msg.payload)

        else:
            self._onMessage(client, userdata, msg)

    def _flushIncomingPayload(self, client, userdata, msg):
        if msg.topic == self.rx_topic:
            self._start_time = time()

        else:
            self._onMessage(client, userdata, msg)

    def _parseHexFile(self, hex_fp):
        bytes_count = 0
        with open(hex_fp, 'r') as f:
            with open(self.hex_stream_fp, 'wb+') as stream_f:
                for line in f:
                    if line[1:3] != '00':
                        nb = int(line[1:3], 16)
                        bytes_count = bytes_count + nb
                        l = line[9:-3]
                        x = [int(l[i:i+2], 16) for i in range(0, len(l)-1, 2)]
                        stream_f.write(struct.pack('B' * len(x), *x))

        return bytes_count

    def _connect(self):
        if self.is_debugging:
            self.debugStop()

        try:
            self.client.unsubscribe(self.rx_topic)
            self.client.unsubscribe(self.status_topic)
            self.client.loop_stop()
            self.client.disconnect()
            self.client.username_pw_set(self.username, self.pw)
            self.client.will_set(topic=self.tx_topic, payload='E')
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()

        except Exception as e:
            self.exceptionLog(e)

    def resetOnMessageCallback(self):
        self.client.on_message = self._onMessage

    def chooseHexFile(self, hex_fp):
        self.flashLog('[INFO] Parsing hex files...')
        self.n_of_bytes = self._parseHexFile(hex_fp)
        self.hex_stream_f = open(self.hex_stream_fp, 'rb')
        self.flashLog('[INFO] Done parsing hex file. Total %d bytes.' % self.n_of_bytes)

    def flashStart(self):
        self.n_packet = 0
        self.sent_bytes = 0
        if self.is_debugging:
            self.debugStop()
            self.client.on_message = self._flushIncomingPayload
            self._start_time = time()

            while (time() - self._start_time) < 1:          # set timeout to flush previous incoming payloads
                pass

        self.client.on_message = self._onMessage_flashing
        if not self.is_connected:
            self._connect()
        
        self._publish('F' + str(self.n_of_bytes))

    def updateBaudrate(self, baudrate):
        if not self.is_connected:
            self._connect()
        self._publish('U' + str(baudrate))

    def debugStart(self):
        if not self.is_connected:
            self._connect()

        self.is_debugging = True
        self.client.on_message = self._onMessage_debugging
        self._publish('D')

    def debugStop(self):
        if not self.is_connected:
            self._connect()

        self.is_debugging = False
        self.client.on_message = self._onMessage
        self._publish('E')

    def resetDevice(self):
        if not self.is_connected:
            self._connect()

        self._publish('R')
  
