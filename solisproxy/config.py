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
import yaml
import json

class Config:
    """ Configuration holder """

    def __init__(self, config):
        self.__config = config

    @staticmethod
    def read(path):
        """ Read configuration from file """
        with open(os.path.join(os.getcwd(), path), "r") as file:
            return Config(yaml.safe_load(file))

    @property
    def listen_address(self):
        """ Server listen address (use 0.0.0.0 to listen on all addresses) """
        return self.__config["server"]["listen_address"]

    @property
    def listen_port(self):
        """ Server listen port """
        return self.__config["server"]["listen_port"]

    @property
    def connection_timeout(self):
        """ Connection timeout """
        return self.__config["server"]["connection_timeout"]

    @property
    def is_forward_enabled(self):
        """ Enables / disables data forwarding to remote server """
        return self.__config["forward"]["enabled"]

    @property
    def forward_primary_address(self):
        """ Primary server address """
        return self.__config["forward"]["primary_address"]

    @property
    def forward_primary_port(self):
        """ Primary server port """
        return self.__config["forward"]["primary_port"]

    @property
    def forward_secondary_address(self):
        """ Secondary server address (used only when primary server is not responding) """
        return self.__config["forward"]["secondary_address"]

    @property
    def forward_secondary_port(self):
        """ Secondary server port """
        return self.__config["forward"]["secondary_port"]

    @property
    def is_mqtt_enabled(self):
        """ Enables / disables data publishing to MQTT broker """
        return self.__config["mqtt"]["enabled"]

    @property
    def mqtt_base_topic(self):
        """ Topic prefix """
        return self.__config["mqtt"]["base_topic"]

    @property
    def mqtt_client_id(self):
        """ Client id """
        return self.__config["mqtt"]["client_id"]

    @property
    def mqtt_server(self):
        """ MQTT broker address """
        return self.__config["mqtt"]["hostname"]

    @property
    def mqtt_port(self):
        """ MQTT broker port """
        return self.__config["mqtt"]["port"]

    @property
    def mqtt_user(self):
        """ Username """
        return self.__config["mqtt"]["username"]

    @property
    def mqtt_password(self):
        """ Password """
        return self.__config["mqtt"]["password"]

    @property
    def mqtt_auth(self):
        return None if not self.mqtt_user else {
            "username": self.mqtt_user, 
            "password": self.mqtt_password
        }

    def __str__(self):
        return json.dumps({
            "listen_address": self.listen_address,
            "listen_port": self.listen_port,
            "connection_timeout": self.connection_timeout,
            "is_forward_enabled": self.is_forward_enabled,
            "forward_primary_address": self.forward_primary_address,
            "forward_primary_port": self.forward_primary_port,
            "forward_secondary_address": self.forward_secondary_address,
            "forward_secondary_port": self.forward_secondary_port,
            "is_mqtt_enabled": self.is_mqtt_enabled,
            "mqtt_base_topic": self.mqtt_base_topic,
            "mqtt_client_id": self.mqtt_client_id,
            "mqtt_server": self.mqtt_server,
            "mqtt_port": self.mqtt_port,
            "mqtt_user": self.mqtt_user,
            "mqtt_password": "***" if self.mqtt_password else ""
        })
