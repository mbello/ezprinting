from typing import Tuple
from cups import Connection
import cups

PRINT_SERVER_GENERIC_NAME = "A Print Server"
DEFAULT_CUPS_HOST = "localhost:631"


class PrintServer:
    _name: str
    _cups_host: str
    _cups_user: str
    _cups_passwd: str

    def __init__(self, name: str):
        self._name = name

    @classmethod
    def cups(cls, *,
             name: str = PRINT_SERVER_GENERIC_NAME,
             host: str = DEFAULT_CUPS_HOST,
             username: str = None,
             password: str = None) -> 'PrintServer':
        self = cls(name=name)
        self._cups_host = host
        self._cups_user = username or ""
        self._cups_passwd = password or ""
        return self

    def test_connection(self) -> Tuple[bool, str]:
        try:
            self.open_connection()
            return True, "Connection OK!"
        except RuntimeError as e:
            return False, str(e)

    def open_connection(self) -> Connection:
        cups.setServer(self._cups_host)
        cups.setUser(self._cups_user)
        cups.setPasswordCB(lambda a: self._cups_passwd)
        return cups.Connection()

    def get_printers(self):
        conn = self.open_connection()
        return conn.getPrinters()
