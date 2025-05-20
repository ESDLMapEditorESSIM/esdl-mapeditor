import time
import unittest

from flask import Flask

#from app import app
from flask_socketio import SocketIO
from sqlalchemy.orm import Session

# from esdl.esdl_handler import EnergySystemHandler
from extensions.data_manager import db
from extensions.data_manager.data_manager import DataManager
from extensions.data_manager.db_model import DataSet

app = Flask(__name__)
socket = SocketIO(app)
dm = DataManager(app, socket)

class DataManagerTestcases(unittest.TestCase):

    @unittest.skip("Test doesn't work with the project manager currently")
    def test_db_insert_data(self):
        import sqlite3
        print("SQLite Version is:", sqlite3.sqlite_version)
        print("DB-API Version is:", sqlite3.version)
        session = db.session
        with app.app_context():
            #ds = db.session.query(DataSet).first()
            esh = EnergySystemHandler()

            #es, parse_info = esh.load_file('esdl/Aa en Hunze ETM.esdl')
            #es, parse_info = esh.load_file('esdl/Drenthe ETM.esdl')
            #es, parse_info = esh.load_file('esdl/RES-Noord-HollandZuid.esdl')
            #es, parse_info = esh.load_file(r'C:\Users\werkmane\OneDrive - TNO\Documents\ESDL\EnergySystems\NWN\OMOTES test case.esdl')
            #es, parse_info = esh.load_file(r'C:\Users\werkmane\OneDrive - TNO\Documents\ESDL\EnergySystems\NWN\OMOTES test case(2).esdl')
            #es, parse_info = esh.load_file(r'C:\Users\werkmane\OneDrive - TNO\Documents\ESDL\EnergySystems\NWN\OMOTES test case_no_storage.esdl')
            #es, parse_info = esh.load_file(r"C:\Users\werkmane\OneDrive - TNO\Documents\ESDL\EnergySystems\EIGEN\EPS - Apeldoorn - Alle maatregelen - Energy Hub - In-line Profiles.esdl")
            es, parse_info = esh.load_file(r"C:\Users\werkmane\OneDrive - TNO\Documents\ESDL\EnergySystems\EIGEN\EPS - Apeldoorn - Alle maatregelen - Energy Hub - In-line Profiles - With Cost Information.esdl")
            #es, parse_info = esh.load_file(r'C:\Users\werkmane\OneDrive - TNO\Documents\ESDL\EnergySystems\NWN\OMOTES test case_with_storage.esdl')
            #es, parse_info = esh.load_file('esdl/Laurens_Ennatuurlijk.esdl')
            #es, parse_info = esh.load_file('esdl/omotes_test_case_no_influxdb.esdl')

            tables = dm.process_esdl(es, owner="ewoud.werkman@tno.nl", scenario_name="Variant no storage")
            session.add_all(tables)
            session.commit()
            ds = [d for d in tables if isinstance(d, DataSet)][0]
            dm.update_filter_options(session, ds)
            time.sleep(0.5)






if __name__ == "__main__":
    unittest.main()
