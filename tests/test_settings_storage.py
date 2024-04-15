import unittest

from extensions.settings_storage import SettingsStorage, SettingType
from src.tno.locking import NamedLocker
import src.settings as settings

TEST_IDENTIFIER = 'test@example.com'

class TestSettingsStorage(unittest.TestCase):
    def setUp(self):
        named_locker = NamedLocker()
        # TODO: Either mock the mongo database or make configuration configurable.
        self.settings_storage = SettingsStorage(
            named_locker,
            database_uri='mongodb://localhost:27017',
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


if __name__ == '__main__':
    unittest.main()
