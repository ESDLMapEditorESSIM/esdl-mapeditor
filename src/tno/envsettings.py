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
import os


class EnvSettings:
    @staticmethod
    def env() -> str:
        return os.getenv("ENV", "dev")

    @staticmethod
    def rabbitmq_queue() -> str:
        return os.getenv("RABBITMQ_QUEUE", "mapeditor")

    @staticmethod
    def rabbitmq_user() -> str:
        return os.getenv("RABBITMQ_USER", "admin")

    @staticmethod
    def rabbitmq_password() -> str:
        return os.getenv("RABBITMQ_PASSWORD", "admin")
