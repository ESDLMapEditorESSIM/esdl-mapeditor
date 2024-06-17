import base64
import unittest
import uuid
from datetime import timezone, datetime
from unittest.mock import patch, MagicMock  # noqa

from esdl import esdl
from esdlproject.ProjectManager import ProjectManager
from extensions.session_manager import PM_KEY
from src.tno.live_model_interface.lmi_listener import on_pm_refresh_request
from src.tno.live_model_interface.shared.message_types import LmiMessage, ProjectManagerMessage
import src.tno.live_model_interface.lmi_listener  # noqa Import the module to patch


class TestOnPmRefreshRequest(unittest.TestCase):
    @patch('src.tno.live_model_interface.lmi_listener.managed_sessions', new_callable=dict)
    @patch('src.tno.live_model_interface.lmi_listener.send_rabbitmq_message', autospec=True)
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
        self.assertEquals(mock_send_rabbitmq_message.call_count, 2)
        args = mock_send_rabbitmq_message.call_args_list[0].args
        self.assertEquals(args[1], "events.pm")
        msg: ProjectManagerMessage = args[0]
        self.assertEquals(msg['client_id'], mocked_client_id1)
        self.assertEquals(msg['project_name'], client1_pm.project.name)
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


if __name__ == '__main__':
    unittest.main()
