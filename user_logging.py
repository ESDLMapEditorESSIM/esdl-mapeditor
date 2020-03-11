import settings
from influxdb import InfluxDBClient
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class UserLogging:
    def __init__(self):
        self.config = settings.user_logging_config
        self.database_client = self.connect_to_database()

    def connect_to_database(self):
        print("Connecting for user_login {}:{} Database:PP{}".format(self.config['host'],
              self.config['port'], self.config['database']))
        client = InfluxDBClient(host=self.config['host'],
              port=self.config['port'], database=self.config['database'])
        # client.drop_database(self.config['database'])
        # client.create_database(self.config['database'])
        return client

    def store_logging(self, user, action=None, command=None, parameters=None, description=None, tags={}):
        if action is not None:
            tags["action"] = action.replace(' ', '_')

        json_body = []
        json_body.append({
            "measurement": "user_logging",
            "time": datetime.now(),
            "tags": tags,
            "fields": {
                "user": user,
                "command": command,
                "parameters": parameters,
                "description": description
            }
        })

        try:
            self.database_client.write_points(points = json_body, database = self.config['database'], batch_size=100)
        except Exception as e:
            logger.error("Error connection to user logging database")