import unittest

import mongomock

from extensions.settings_storage import SettingsStorage, SettingType
from src.tno.locking import NamedLocker

MONGO_TEST_SERVER_HOST = "mongo.unittests.com"
MONGO_TEST_SERVER_PORT = 27017
TEST_IDENTIFIER = 'test@example.com'


class TestSettingsStorage(unittest.TestCase):
    @mongomock.patch(servers=((MONGO_TEST_SERVER_HOST, MONGO_TEST_SERVER_PORT),))
    def setUp(self):
        named_locker = NamedLocker()
        self.settings_storage = SettingsStorage(
            named_locker,
            database_uri=f"mongodb://{MONGO_TEST_SERVER_HOST}:{MONGO_TEST_SERVER_PORT}/test_db",
        )

    def test_set_get(self):
        expected_value = 'test_value'

        # Do set, check if a lock was created.
        self.assertNotIn(TEST_IDENTIFIER, self.settings_storage.named_locker.locks)
        self.settings_storage.set(SettingType.USER, TEST_IDENTIFIER, 'test_key', expected_value)
        self.assertIn(TEST_IDENTIFIER, self.settings_storage.named_locker.locks)

        get_value = self.settings_storage.get(SettingType.USER, TEST_IDENTIFIER, 'test_key')
        self.assertEqual(get_value, expected_value)
        self.settings_storage.delete(SettingType.USER, TEST_IDENTIFIER, 'test_key')
        try:
            self.settings_storage.get(SettingType.USER, TEST_IDENTIFIER, 'test_key')
            self.fail('Expected KeyError')
        except KeyError:
            pass

    def test_delete(self):
        expected_value = 'test_value'
        self.settings_storage.set(SettingType.USER, TEST_IDENTIFIER, 'test_key', expected_value)
        self.settings_storage.delete(SettingType.USER, TEST_IDENTIFIER, 'test_key')
        try:
            self.settings_storage.get(SettingType.USER, TEST_IDENTIFIER, 'test_key')
            self.fail('Expected KeyError')
        except KeyError:
            pass

        has_value = self.settings_storage.has(SettingType.USER, TEST_IDENTIFIER, 'test_key')
        self.assertIs(has_value, False)

    def test_has(self):
        expected_value = 'test_value'

        has_value = self.settings_storage.has(SettingType.USER, TEST_IDENTIFIER, 'test_key')
        self.assertIs(has_value, False)
        self.settings_storage.set(SettingType.USER, TEST_IDENTIFIER, 'test_key', expected_value)

        final_has_value = self.settings_storage.has(SettingType.USER, TEST_IDENTIFIER, 'test_key')
        self.assertIs(final_has_value, True)


if __name__ == '__main__':
    unittest.main()
