import settings
from influxdb import InfluxDBClient
from datetime import datetime
import logging
import threading
from queue import Queue

logger = logging.getLogger(__name__)


class UserLogging:
    def __init__(self):
        self.config = settings.user_logging_config
        self.queue = Queue()
        self.database_client = self.connect_to_database()
        self.writer_thread = threading.Thread(target=self._writer_thread_function, name='Influx-Writer-Thread')
        self.writer_thread.start()


    def connect_to_database(self):
        print("Connecting for user_login {}:{} Database: {}".format(self.config['host'],
              self.config['port'], self.config['database']))
        client = InfluxDBClient(host=self.config['host'],
              port=self.config['port'], database=self.config['database'])
        # client.drop_database(self.config['database'])
        # client.create_database(self.config['database'])
        return client

    def store_logging(self, user, action=None, command=None, parameters=None, description=None, tags={}):
        if settings.USER_LOGGING_ENABLED:
            if action is not None:
                tags["action"] = action.replace(' ', '_')

            json_body = {
                "measurement": "user_logging",
                "time": datetime.now(),
                "tags": tags,
                "fields": {
                    "user": user,
                    "command": command,
                    "parameters": parameters,
                    "description": description
                }
            }

            self.queue.put_nowait(json_body)


    def _writer_thread_function(self):
        point_list = list()
        while True:
            if not self.database_client:
                logger.error("Error connecting to user logging database. Logging is ignored")
                return
            json = self.queue.get() # this call blocks if nothing is in the queue
            point_list.append(json)
            self.queue.task_done()
            while not self.queue.empty(): # check if there are more points to write in a batch
                json = self.queue.get()
                point_list.append(json)
                self.queue.task_done()
            logger.debug('User logging {} points to InfluxDB'.format(len(point_list)))
            try:
                self.database_client.write_points(points=point_list, database=self.config['database'])
                point_list.clear()
            except Exception as e:
                logger.error("Error connecting to user logging database. NOT LOGGING ANYTHING! {}".format(e))
                point_list.clear() # throw points away that can't be written
