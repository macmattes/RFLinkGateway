#RFLink Gateway to MQTT

##Purpose
Bridge between RFLink Gateway and MQTT broker.

##Current features
Forwarding messages received on TTY port from RFLink Gateway Arduino board
to MQTT broker in both directions.

Every message received from RFLinkGateway is split into single parameters
and published to different MQTT topics.
Example:
Message:
`20;83;Oregon Rain2;ID=2a19;RAIN=002a;RAINTOT=0054;BAT=OK;`

 is translated to following topics:

 `stat/data/RFLINK/Oregon Rain2/2a19/RAIN 002a`

 `stat/data/RFLINK/Oregon Rain2/2a19/RAINTOT 0054`

 `stat/data/RFLINK/Oregon Rain2/2a19/BAT OK`




Every message received on particular MQTT topic is translated to
RFLink Gateway and sent to 433 MHz.

##Configuration

Whole configuration is located in config.json file.

```json
{
  "mqtt_host": "your.mqtt.host",
  "mqtt_port": 1883,
  "mqtt_prefix": "RFLINK",
  "rflink_tty_device": "/dev/ttyUSB0",
  "rflink_direct_output_params": ["BAT", "CMD", "SET_LEVEL", "SWITCH", "HUM", "CHIME", "PIR", "SMOKEALERT"]
}
```

config param | meaning
-------------|---------
| mqtt_host | MQTT broker host |
| mqtt_port | MQTT broker port|
| mqtt_prefix | prefix for publish (stat/prefix/...) and subscribe (cmnd/prefix/...) topic| 
| rflink_tty_device | Arduino tty device |
| rflink_ignored_devices | Parameters transferred to MQTT without any processing|

##Output data
Application pushes informations to MQTT broker in following format:
standard: if extended topic not defined
stat/[mqtt_prefix]/[device_type]/[device_id]/[parameter]

extended: if extended topic for 'SWITCH' is defined
stat/[mqtt_prefix]/[device_type]/[device_id]/[device_port]/[parameter]

'stat/RFLink/BrelMotor/e440ab/c4 STOP'

Every change should be published to topic:
cmnd/[mqtt_prefix]/[device_type]/[device_id]/[switch_ID]

`cmnd/data/RFLINK/TriState/8556a8/1 ON`


##References
- RFLink Gateway project http://www.nemcon.nl/blog2/
- RFLink Gateway protocol http://www.nemcon.nl/blog2/protref
