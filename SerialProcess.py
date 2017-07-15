import logging
import multiprocessing
import time

import serial


#TODO keepalive i obsluga resetu


class SerialProcess(multiprocessing.Process):
    def __init__(self, messageQ, commandQ, config):
        self.logger = logging.getLogger('RFLinkGW.SerialProcessing')

        self.logger.info("Starting...")
        multiprocessing.Process.__init__(self)

        self.messageQ = messageQ
        self.commandQ = commandQ

        self.gatewayPort = config['rflink_tty_device']
        self.sp = serial.Serial()
        self.connect()

        self.processing_exception = config['rflink_direct_output_params']
        self.processing_extendedtopic = config['rflink_extendedtopic_params']

    def close(self):
        self.sp.close()
        self.logger.debug('Serial closed')

    def prepare_output(self, data_in):
        out = []
        data = data_in.decode("ascii").replace(";\r\n", "").split(";")
        self.logger.debug("Received message:%s" % (data))
        if len(data) > 3 and data[0] == '20':
            family = data[2]
            deviceId = data[3].split("=")[1]
            d = {}
            xkey = False
            longkey = ""
            for t in data[4:]:
                token = t.split("=")
                d[token[0]] = token[1]
            for key in d:
                if key in self.processing_extendedtopic:
                    xkey = True
                if key in self.processing_exception:
                   	val = d[key]
               	else:
                    val = int(d[key], 16) / 10
                if not xkey:
                    topic_out = "stat/%s/%s/%s" % (family, deviceId, key)
                    data_out = {
                  		'method': 'publish',
                   		'topic': topic_out,
                   		'family': family,
                   		'deviceId': deviceId,
                  	 	'param': key,
                  	 	'payload': val,
                  	 	'qos': 1,
                  	 	'timestamp': time.time()
                    }
                    out = out + [data_out]
                else:
                    if longkey == "":
                        if key == sorted(d.keys())[-1]:
                            longkey = str(val)
                        else:
                            longkey = key
                    else:
                        if key == sorted(d.keys())[-1]:
                           longkey = longkey + "/" + str(val)
                        #else:
                           #longkey = longkey + "/" + key
            if xkey:
                topic_out = "stat/%s/%s/%s" % (family, deviceId, longkey)
                data_out = {
                  	'method': 'publish',
                   	'topic': topic_out,
                  	'family': family,
               		'deviceId': deviceId,
               	 	'param': longkey,
               	 	'payload': val,
               	 	'qos': 1,
               	 	'timestamp': time.time()
           		}
                out = out + [data_out]			
        return out

    def prepare_input(self, task):
        out_str =  '10;%s;%s;%s;%s;\n' % (task['family'], task['deviceId'], task['param'], task['payload'])
        self.logger.debug('Sending to serial:%s' % (out_str))
        return out_str

    def connect(self):
        self.logger.info('Connecting to serial')
        while not self.sp.isOpen():
            try:
                self.sp = serial.Serial(self.gatewayPort, 57600, timeout=1)
                self.logger.debug('Serial connected')
            except Exception as e:
                self.logger.error('Serial port is closed %s' % (e))

    def run(self):
        self.sp.flushInput()
        while True:
            try:
                if not self.commandQ.empty():
                    task = self.commandQ.get()
                    # send it to the serial device
                    self.sp.write(self.prepare_input(task).encode('ascii'))
            except Exception as e:
                self.logger.error("Send error:%s" % (format(e)))
            try:
                if (self.sp.inWaiting() > 0):
                    data = self.sp.readline()
                    task_list = self.prepare_output(data)
                    for task in task_list:
                        self.logger.debug("Sending to Q:%s" % (task))
                        self.messageQ.put(task)
                else:
                    time.sleep(0.01)
            except Exception as e:
                self.logger.error('Receive error: %s' % (e))
                self.connect()
