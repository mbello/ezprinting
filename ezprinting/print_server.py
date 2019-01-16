# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import cups
import json
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession


SERVER_TYPE_CUPS = "CUPS"
SERVER_TYPE_GOOGLE_CLOUD_PRINT = "GCP"

PRINT_SERVER_GENERIC_NAME="A Print Server"

DEFAULT_CUPS_HOST="localhost:631"

GCP_SCOPEs = ['https://www.googleapis.com/auth/cloudprint']
GCP_BASE_URI = 'https://www.google.com/cloudprint'


class PrintServer:
    def __init__(self, name, server_type, params_dict):
        self._name = name
        self._type = server_type
        self.is_cups = False
        self.is_gcp = False
        if (self._type == SERVER_TYPE_CUPS):
            self.is_cups = True
            self._cups_host = params_dict["cups_host"]
            self._cups_user = params_dict["cups_username"]
            self._cups_passwd = params_dict["cups_password"]
            self._cups_user = "" if not self._cups_user else self._cups_user
            self._cups_passwd = "" if not self._cups_passwd else self._cups_password
        elif (self._type == SERVER_TYPE_GOOGLE_CLOUD_PRINT):
            self.is_gcp = True
            self._service_account_json = params_dict
        else:
            raise ValueError("Invalid server_type.")

    @classmethod
    def cups(cls, host=DEFAULT_CUPS_HOST, username: str = None, password: str = None, name=PRINT_SERVER_GENERIC_NAME):
        d = dict()
        d["cups_host"] = host
        d["cups_username"] = username
        d["cups_password"] = password
        d["name"] = name
        return cls(name=name, server_type=SERVER_TYPE_CUPS, params_dict=d)

    @classmethod
    def gcp(cls, service_account: str, name: str=PRINT_SERVER_GENERIC_NAME):
        return cls(name=name, server_type=SERVER_TYPE_GOOGLE_CLOUD_PRINT, params_dict=json.loads(service_account, strict=False))

    def test_connection(self):
        success = True
        error_message = "Connection OK!"

        if self.is_cups:
            try:
                conn = self.open_connection()
            except RuntimeError as e:
                success = False
                error_message = str(e)

        elif self.is_gcp:
            try:
                session = self.open_connection()
                r = session.get("{}{}".format(GCP_BASE_URI, '/search?use_cdd=true&connection_status=ALL'))
            except Exception as e:
                success = False
                error_message = str(e)
            else:
                if not r.ok:
                    success = False
                    error_message = r.reason
                session.close()

        return success, error_message

    def open_connection(self):
        if (self.is_cups):
            cups.setServer(self._cups_host)
            cups.setUser(self._cups_user)
            cups.setPasswordCB(lambda a: self._cups_passwd)
            return cups.Connection()
        elif (self.is_gcp):
            credentials = service_account.Credentials.from_service_account_info(self._service_account_json, scopes=GCP_SCOPEs)
            return AuthorizedSession(credentials)
        else:
            raise RuntimeError("Server type error!")

    def get_printers(self):
        if self.is_cups:
            conn = self.open_connection()
            return conn.getPrinters()
        elif self.is_gcp:
            session = self.open_connection()
            r = session.get(GCP_BASE_URI + '/search?use_cdd=true&extra_fields=connectionStatus&q=&type=&connection_status=ALL')
            j = json.loads(r.content, strict=False)
            return j['printers']