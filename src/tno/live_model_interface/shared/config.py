#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO
import pika

from src.tno.envsettings import EnvSettings

RABBITMQ_APP_ID = "esdl-mapeditor"

PIKA_CONNECTION_PARAMETERS = pika.ConnectionParameters(
    host=EnvSettings.rabbitmq_host(),
    port=EnvSettings.rabbitmq_port(),
    credentials=pika.PlainCredentials(
        EnvSettings.rabbitmq_user(), EnvSettings.rabbitmq_password()
    ),
)

AMQP_URL = f"amqp://{EnvSettings.rabbitmq_user()}:{EnvSettings.rabbitmq_password()}@{EnvSettings.rabbitmq_host()}:{EnvSettings.rabbitmq_port()}"
