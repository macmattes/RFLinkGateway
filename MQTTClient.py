import logging
import multiprocessing
import time

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish


class MQTTClient(multiprocessing.Process):
    def __init__(self, messageQ, commandQ):
        self.logger = logging.getLogger('RFLinkGW.MQTTClient')
        self.logger.info("Starting...")

        multiprocessing.Process.__init__(self)
        self.messageQ = messageQ
        self.commandQ = commandQ

        self.mqttDataPrefix = '/data/RFLINK'
        self._mqttConn = mqtt.Client(client_id='RFLinkGateway')
        self._mqttConn.connect('127.0.0.1', port=1883, keepalive=120)
        self._mqttConn.on_disconnect = self._on_disconnect
        self._mqttConn.on_publish = self._on_publish
        self._mqttConn.on_message = self._on_message

    def close(self):
        self.logger.info("Closing connection")
        self._mqttConn.disconnect()

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.logger.error("Unexpected disconnection.")
            self._mqttConn.reconnect()

    def _on_publish(self, client, userdata, mid):
        self.logger.debug("Message " + str(mid) + " published.")

    def _on_message(self, client, userdata, message):
        self.logger.debug("Message received: %s" % (message))

        data = message.topic.replace(self.mqttDataPrefix + "/", "").split("/")
        data_out = {
            'method': 'subscribe',
            'topic': message.topic,
            'family': data[0],
            'deviceId': data[1],
            'param': data[3],
            'payload': message.payload.decode('ascii'),
            'qos': 1
        }
        self.commandQ.put(data_out)

    def publish(self, task):
        topic = "%s/%s/%s/R/%s" % (self.mqttDataPrefix, task['family'], task['deviceId'], task['param'])
        try:
            publish.single(topic, payload=task['payload'])
            self.logger.debug('Sending:%s' % (task))
        except Exception as e:
            self.logger.error('Publish problem: %s' % (e))
            self.messageQ.put(task)

    def run(self):
        # self._mqttConn.message_callback_add("/data/RFLINK/+/+/W/+", self._on_message)
        self._mqttConn.subscribe("/data/RFLINK/+/+/W/+")
        while True:
            if not self.messageQ.empty():
                task = self.messageQ.get()
                if task['method'] == 'publish':
                    self.publish(task)
            else:
                # self._mqttConn.loop_read()
                time.sleep(0.01)
            self._mqttConn.loop()