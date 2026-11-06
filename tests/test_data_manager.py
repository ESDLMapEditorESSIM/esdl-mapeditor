import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from flask import Flask
from flask_socketio import SocketIO

from esdl import esdl
from esdl.project.ProjectManager import ProjectManager
from extensions.data_manager import db
from extensions.data_manager.data_manager import DataManager
from extensions.data_manager.db_model import Data, DataSet
from extensions.settings_storage import SettingsStorage


class DataManagerTestcases(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.app = Flask(__name__)
        database_uri = f"sqlite:///{self.temp_dir.name}/data_manager.db"
        with patch("extensions.data_manager.data_manager.settings.SQLALCHEMY_DATABASE_URI", database_uri):
            self.dm = DataManager(self.app, SocketIO(self.app), Mock(spec=SettingsStorage))

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_db_insert_data(self) -> None:
        """Persist an energy system's asset data and filter options."""
        pm = ProjectManager()
        es = pm.get_active_energy_system()
        turbine = esdl.WindTurbine(id="wind-turbine", name="Wind turbine", power=1500.0)
        es.instance[0].area.asset.append(turbine)
        owner = "test@example.com"

        with self.app.app_context():
            tables = self.dm.process_esdl(es, owner=owner, energy_unit="")
            db.session.add_all(tables)
            db.session.commit()
            dataset = db.session.query(DataSet).one()
            self.dm.update_filter_options(db.session, dataset)
            data = db.session.query(Data).one()

            self.assertEqual(dataset.energy_system_id, es.id)
            self.assertEqual(dataset.created_by, owner)
            self.assertEqual(data.dataset_id, dataset.id)
            self.assertEqual(data.value, turbine.power)
            self.assertEqual(data.variable.name, "Power (W)")


if __name__ == "__main__":
    unittest.main()
