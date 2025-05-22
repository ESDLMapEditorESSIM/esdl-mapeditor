import threading
import unittest
import uuid
from pathlib import Path

import pika
from pika.exchange_type import ExchangeType

from esdl.processing.string_uri import StringURI
from esdlproject.ProjectManager import ProjectManager
from src.tno.envsettings import EnvSettings
from src.tno.live_model_interface.api import activate_live_model_interface

from extensions.session_manager import managed_sessions, PM_KEY
from src.tno.live_model_interface.shared.config import PIKA_CONNECTION_PARAMETERS

rve_application_context = {
  "application_id": "rve",
  "name": "Ruimte voor Energie",
  "live_model_interfaces": [
    {
      "lmi_id": "connect-nearest-infra",
      "name": "Connect Nearest Infra",
      "description": "Automatically connect new assets to the transformer of the DSO service area in which the asset is placed",
      "enabled": True,
      "can_be_disabled": True
    }
  ],
  "is_global": True
}

cni_lmi = rve_application_context["live_model_interfaces"][0]


@unittest.skip("Work in progress")
class RveProjectManagerTest(unittest.TestCase):

    def setUp(self):
        self.received = threading.Event()
        self.received_body = None

        # open connection & channel
        self.conn = pika.BlockingConnection(
            parameters=PIKA_CONNECTION_PARAMETERS
        )
        self.ch   = self.conn.channel()

        # declare the exchange (must match what your code uses)
        self.ch.exchange_declare(exchange=EnvSettings.rabbitmq_exchange(), exchange_type=ExchangeType.topic, durable=True)

        # create an anonymous, exclusive queue and bind it
        q = self.ch.queue_declare(queue='', exclusive=True)
        self.queue_name = q.method.queue
        self.ch.queue_bind(
            exchange=EnvSettings.rabbitmq_exchange(),
            queue=self.queue_name,
            routing_key="lmi.#"
        )

        def _on_message(ch, method, properties, body):
            self.received_body = body
            self.received.set()
            self.lmi_message_handler(body)

        self.ch.basic_consume(
            queue=self.queue_name,
            on_message_callback=_on_message,
            auto_ack=True
        )

        # start consuming in background
        self._consumer_thread = threading.Thread(target=self.ch.start_consuming, daemon=True)
        self._consumer_thread.start()

        # Set up project manager and load project file.
        self.resources_path = Path("tests/resources")
        self.project_file = self.resources_path / "Drenthe_huidig_met_IIS.project"
        self.pm = ProjectManager(create_empty_variant=False)

        self.assertTrue(self.project_file.exists(), f"Project file not found: {self.project_file}")

        with open(self.project_file, 'r', encoding='utf-8') as f:
            project_content = f.read()

        uri = StringURI(str(self.project_file.name), project_content)
        self.project = self.pm.load(uri)

        # Mock session data.
        self.client_id = str(uuid.uuid4())

        managed_sessions.update({
            self.client_id: {
                PM_KEY: self.pm,
            },
        })
        activate_live_model_interface(cni_lmi["lmi_id"], self.client_id)
        got_it = self.received.wait(timeout=5.0)
        self.assertTrue(got_it, "Did not receive lmi.pm.refresh message in time")
        print(self.received_body)

    def lmi_message_handler(self, body: bytes):
        """
        This is the handler that should be called when we get
        a message on lmi.pm.refresh.  You can deserialize & act here.
        """
        print("Got message:", body)

    def test_load_project(self):
        """Test loading a project file using the ProjectManager"""
        # Verify the project was loaded successfully
        self.assertIsNotNone(self.project, "Project should not be None")
        self.assertTrue(len(self.pm.project.variantCollection) == 2, "Project should have two variant collections")

        # Test that there is an active variant
        active_variant = self.pm.get_active_variant()
        self.assertIsNotNone(active_variant, "Active variant should not be None")

        # Test getting the active energy system
        active_es = self.pm.get_active_energy_system()
        self.assertIsNotNone(active_es, "Active energy system should not be None")
        self.assertIsNotNone(active_es.id, "Energy system should have an ID")

    def add_windturbine(self):
        pass


if __name__ == '__main__':
    unittest.main()
