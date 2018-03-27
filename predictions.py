from dateutil import parser
from tzlocal import get_localzone
from logging.config import dictConfig

import requests
import yaml
import os
import pytds
import datetime
import pytz
import logging

BASE_DIR = os.path.dirname(__file__)
with open(os.path.abspath("config.yaml")) as f:
    CONFIG = yaml.load(f.read())

LOG_LEVEL = CONFIG.get('log_level', 'DEBUG')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] [%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'verbose': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': LOG_LEVEL,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
        'file_handler': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'level': LOG_LEVEL,
            'filename': os.path.join(BASE_DIR, 'predictions.log'),
            'when': 'midnight',
            'backupCount': 10,
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file_handler'],
            'level': LOG_LEVEL,
            'propagate': True
        }
    }
}
dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class Configuration:
    def __init__(self, configuration):
        self.api_uri = configuration['api_endpoint']
        self.api_token = configuration['api_token']
        self.field_mappings = configuration['response_to_field']
        self.db_timestamp_field = configuration['database_timestamp_field']
        self.db_server = configuration['sql']['server']
        self.database = configuration['sql']['database']
        self.db_username = configuration['sql']['username']
        self.db_password = configuration['sql']['password']
        self.db_table = configuration['sql']['table']
        self.adjust_time = configuration['adjust_UTC_to_Local_time']


class ProcessPrediction:
    def __init__(self, configuration):
        self.configuration = configuration
        self.full_prediction = None
        self.selected_data = None

    def get_prediction(self):
        """
        Call the API to get the latest Prediction and subset based on the data we want to put into the Database
        :return:
        """
        response = requests.get(self.configuration.api_uri,
                                headers={'Authorization': 'token ' + self.configuration.api_token})
        if response.ok:
            self.full_prediction = response.json()['results'][0]
            logger.debug('Response: {0}'.format(self.full_prediction))
            self.selected_data = self._map_response_to_db_fields()
            logger.debug('Selected Data: {0}'.format(self.selected_data))
        else:
            logger.error('Could not connect to API')
            logger.error(response)
        self.update_db()

    def update_db(self):
        # Format the timestamp to be in SQL Format
        dt = parser.parse(self.selected_data[self.configuration.db_timestamp_field])
        # Adjust from UTC Time to Local Time of flag set
        if self.configuration.adjust_time:
            local_tz = get_localzone()
            dt = dt.replace(tzinfo=pytz.utc).astimezone(local_tz)

        dt = datetime.datetime.strftime(dt, "%Y%m%d %I:%M:%S %p")
        self.selected_data[self.configuration.db_timestamp_field] = dt

        fields = ",".join(str(x) for x in list(self.selected_data.keys()))
        values = ",".join("'" + x + "'" if isinstance(x, str) else str(x) for x in list(self.selected_data.values()))
        # Create insert statement as
        # INSERT INTO customers (Field1, Field2) VALUES ('value1',1)
        data_to_insert = "INSERT INTO {0} ({1}) VALUES ({2})".format(self.configuration.db_table,
                                                                     str(fields),
                                                                     str(values))
        logger.debug("Running the following SQL Command: {0}".format(data_to_insert))
        with pytds.connect(self.configuration.db_server, self.configuration.database, self.configuration.db_username, self.configuration.db_password) as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(data_to_insert)
                except pytds.tds_base.IntegrityError as e:
                    logger.error('Duplicate key Error')
                    logger.error(e)
            conn.commit()
            conn.close()

    def _map_response_to_db_fields(self):
        """
        Map the API Response fields to the Database Field Names
        :return: Dictionary of the fields to write to the database
        """
        selected_data = dict()
        # Loop Over other fields and get the ones we want
        for mapping in self.configuration.field_mappings:
            for key, value in mapping.items():
                selected_data[value] = self.full_prediction['prediction'][key]
        return selected_data


config = Configuration(CONFIG)
ProcessPrediction(config).get_prediction()
