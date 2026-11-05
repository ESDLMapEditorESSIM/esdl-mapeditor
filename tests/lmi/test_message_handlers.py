import base64
import unittest
import uuid
from datetime import timezone, datetime
from unittest.mock import patch, MagicMock  # noqa

from flask import Flask, current_app, has_app_context, has_request_context, request, session

from esdl import esdl
from esdl.project.ProjectManager import ProjectManager, eobject_to_string, ESDLFormat
from extensions.session_manager import PM_KEY
from src.incremental_ui import ui_change_handler
from src.tno.live_model_interface.lmi_listener import on_high_level_change, on_pm_refresh_request
from src.tno.live_model_interface.shared.message_types import LmiMessage, ProjectManagerMessage
import src.tno.live_model_interface.lmi_listener  # noqa Import the module to patch


class TestOnPmRefreshRequest(unittest.TestCase):
    @patch('src.tno.live_model_interface.api.managed_sessions', new_callable=dict)
    @patch('src.tno.live_model_interface.api.send_rabbitmq_message', autospec=True)
    def test_on_pm_refresh_request(self, mock_send_rabbitmq_message, mock_managed_sessions):
        # Arrange
        client1_pm = ProjectManager()
        client1_pm.project.name = "Project1"
        client1_variant = client1_pm.active_variant
        client1_variant.name = "Variant1"
        client1_es = client1_pm.get_active_energy_system()

        variant1_stack = client1_pm.get_undo_redo_stack(client1_es)
        with variant1_stack.track_changes("Add pipe1"):
            pipe1 = esdl.Pipe(name="pipe1")
            client1_es.instance[0].area.asset.append(pipe1)

        mock_message: LmiMessage = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime(2023, 1, 1, tzinfo=timezone.utc),
            'client_id': None,
            'user_email': None,
        }
        # Add two clients to the managed sessions.
        mocked_client_id1 = str(uuid.uuid4())
        mocked_client_id2 = str(uuid.uuid4())
        mock_managed_sessions.update({
            mocked_client_id1: {
                PM_KEY: client1_pm,
            },
            mocked_client_id2: {
                PM_KEY: ProjectManager(),
            },
        })

        # Act
        on_pm_refresh_request(mock_message)

        # Assert
        mock_send_rabbitmq_message.assert_called()
        self.assertEqual(mock_send_rabbitmq_message.call_count, 2)
        args = mock_send_rabbitmq_message.call_args_list[0].args
        self.assertEqual(args[1], "events.pm")
        msg: ProjectManagerMessage = args[0]
        self.assertEqual(msg['client_id'], mocked_client_id1)
        self.assertEqual(msg['project_name'], client1_pm.project.name)
        b64_project = msg['b64_project']
        second_pm = ProjectManager()
        project_string = base64.b64decode(b64_project).decode()
        second_pm.load_from_string(project_string)
        assert second_pm.project.name == client1_pm.project.name
        assert second_pm.active_variant.name == client1_variant.name

        # Check if the pipe is in the second_pm
        client1_es = second_pm.get_active_energy_system()
        assert len(client1_es.instance[0].area.asset) == 1
        found_pipe1 = False
        for asset in client1_es.instance[0].area.asset:
            if asset.name == "pipe1":
                found_pipe1 = True
        self.assertTrue(found_pipe1)


class TestOnHighLevelChange(unittest.TestCase):
    def test_updates_ui_in_app_context(self):
        """LMI changes supply Flask context without storing the app in the undo stack."""
        app = Flask(__name__)
        app.secret_key = str(uuid.uuid4())
        source_pm = ProjectManager()
        pm = ProjectManager()
        pm.load_from_string(source_pm.save())
        stack = source_pm.get_undo_redo_stack()
        with stack.track_changes("Rename energy system"):
            source_pm.get_active_energy_system().name = "Renamed"
        message = {
            "client_id": "client",
            "variant_id": source_pm.active_variant.id,
            "high_level_change": eobject_to_string(stack.top, ESDLFormat.JSON),
        }
        pm.add_change_listener("ui", ui_change_handler.change_handler)

        def process_energy_system(**kwargs):
            self.assertIs(current_app._get_current_object(), app)
            self.assertEqual(session["client_id"], "client")
            self.assertEqual(request.sid, "socket")
            self.assertEqual(request.namespace, "/esdl")

        with (
            patch("src.tno.live_model_interface.lmi_listener.LOCAL_APP", app),
            patch("src.tno.live_model_interface.lmi_listener.get_project_manager_for_client_id", return_value=pm),
            patch.object(ui_change_handler, "managed_sessions", {"client": {"socketio_sid": "socket"}}),
            patch.object(
                ui_change_handler.call_process_energy_system, "submit", side_effect=process_energy_system
            ) as submit,
        ):
            on_high_level_change(message)

        self.assertEqual(pm.get_active_energy_system().name, "Renamed")
        submit.assert_called_once_with(force_update_es_id=pm.get_active_energy_system().id, zoom=False)
        self.assertFalse(hasattr(pm.get_undo_redo_stack().change_context, "flask_app"))
        self.assertFalse(has_app_context())
        self.assertFalse(has_request_context())


if __name__ == '__main__':
    unittest.main()
