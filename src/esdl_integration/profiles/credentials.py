from dataclasses import dataclass


@dataclass
class Credentials:
    """
    Simple dataclass that contains username and password used for logging into a database

    Use the static function create_dict() to create a compatible dict to be used in the DataTableProfileManager
    load() and save() methods for authentication
    """

    username: str
    password: str

    @staticmethod
    def create_dict(id: str, username: str, password: str) -> dict[str, "Credentials"]:
        """
        Creates a new credential dict with a mapping from id -> Credential[Username, Password] which can be used directly
        in the load() and save() methods of the DataTableProfileManager class
        :param id: refers to the id of the DatabaseConfiguration for which these credentials should be used. Alternatively
                    you can use the hostname as id, for more generic matching.
        :param username: Username
        :param password: Password
        :return: dict[str, 'Credentials']
        """
        d = dict()
        d[id] = Credentials(username, password)
        return d
