"""
Solis-Proxy
Copyright (C) 2021 rATse

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import shutil
import json
import yaml
import logging
import logging.config
import socket
import sys
import binascii
import threading
import paho.mqtt.publish as publish

from solarman import Solarman
from config import Config

CONFIG_DIR = "config"
APP_CONFIG_FILE = "config.yml"
LOG_CONFIG_FILE = "logging.yml"

# Load logger configuration file
with open(os.path.join(CONFIG_DIR, LOG_CONFIG_FILE), "r") as file:
    logging.config.dictConfig(yaml.safe_load(file))
logger = logging.getLogger()

# Load server configuration file
config = Config.read(os.path.join(CONFIG_DIR, APP_CONFIG_FILE))
logger.info("Configuration loaded: %s", config)

# Map: Frame type -> Topic name
MQTT_TOPIC_MAP = {
    Solarman.FRAME_TYPE_INFORMATION: "information",
    Solarman.FRAME_TYPE_DATA: "data"
}

def send_data(data, server_address, server_port):
    """ Send data to remote server """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_socket:
        remote_socket.settimeout(10)
        logger.info("Connecting to remote server [%s:%d]", server_address, server_port)

        try:
            remote_socket.connect((server_address, server_port))
            logger.info("Connection established")
        except:
            logger.error("Connection error")
            return False
                
        try:
            remote_socket.sendall(data)
            logger.info("Sending data completed")
        except:
            logger.error("Sending data error")
            return False

        try:
            recv = remote_socket.recv(1024)
            logger.debug("Data received: %s", binascii.hexlify(recv))
        except TimeoutError:
            pass

    return True


def forward(data):
    """ Forward data to remote server """

    result = send_data(data, config.forward_primary_address, config.forward_primary_port)
    if not result:
        send_data(data, config.forward_secondary_address, config.forward_secondary_port)


def publish_mqtt(message, topic_name):
    """ Send message to MQTT broker """

    topic = [config.mqtt_base_topic]
    for name in topic_name:
        topic.append(str(name))

    mqtt_topic = "/".join(topic)
    logger.debug("MQTT topic: %s", mqtt_topic)

    publish.single(mqtt_topic, message, client_id=config.mqtt_client_id, hostname=config.mqtt_server, auth=config.mqtt_auth)
    logger.info("Publishing data to MQTT broker completed")


def start():
    """ Start proxy server """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((config.listen_address, config.listen_port))
        server_socket.listen(1)

        while True:
            logger.info("Waiting for a connection...")

            connection, address = server_socket.accept()
            connection.settimeout(config.connection_timeout)

            logger.info("Connection from %s", address)

            try:
                # Receive data
                rawdata = connection.recv(1024)
                if len(rawdata) == 0:
                    continue

                hexdata = binascii.hexlify(rawdata)
                logger.debug("Hexdata (length: %d): %s", len(hexdata), hexdata)

                # Forward data to remote server
                if config.is_forward_enabled:
                    forward_thread = threading.Thread(target=forward, args=(rawdata,))
                    forward_thread.start()

                # Create Solarman object for data processing
                solarman = Solarman(rawdata)

                # Get payload
                try:
                    payload = solarman.get_payload()
                except Solarman.UnsupportedFrameTypeError as uftex:
                    logger.warning("Unsupported frame type: %s", uftex.frame_type)
                else:
                    message = json.dumps(payload)
                    logger.info("Payload: %s", message)

                    # Publish data over MQTT
                    if config.is_mqtt_enabled:
                        publish_mqtt(message, [solarman.get_data_logger_serial_no(), MQTT_TOPIC_MAP.get(solarman.get_frame_type())])

                # Send response if needed
                response = solarman.get_response()
                if response is not None:
                    logger.debug("Response: %s", binascii.hexlify(response))
                    connection.sendall(response)

            except Solarman.ValidationError as vex:
                logger.error("Data validation error: %s", vex)
            except TimeoutError:
                logger.error("Socket timeout")
            except Exception:
                logger.error("Something goes wrong: %s", sys.exc_info()[1])
            finally:
                logger.info("Disconnected")
                connection.shutdown(socket.SHUT_RDWR)
