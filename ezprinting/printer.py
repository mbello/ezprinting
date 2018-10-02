# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import json
import cups
from ezprinting.print_server import PrintServer, GCP_BASE_URI


class Printer:

    def __init__(self, print_server: PrintServer, name_or_id: str):
        self.print_server = print_server
        self.id = name_or_id

    def check_printer_exists(self, conn=None):
        if not conn:
            conn = self.print_server.open_connection()

        if self.print_server.is_cups:
            try:
                p = self.get_printer_attributes(conn=conn)
            except cups.IPPError:
                return False

            return True if p['printer-name'] == self.id else False

        elif self.print_server.is_gcp:
            p = self.get_printer_attributes(conn=conn)
            if not p['success']:
                self.enable_printer(conn=conn)
                p = self.get_printer_attributes(conn=conn)
            return p['success']

    def get_printer_attributes(self, conn=None):
        if not conn:
            conn = self.print_server.open_connection()

        if self.print_server.is_cups:
            return conn.getPrinterAttributes(self.id)
        elif self.print_server.is_gcp:
            r = conn.get('{}/printer?printerid={}'.format(GCP_BASE_URI, self.id))
            j = json.loads(r.content, strict=False)
            return j

    def enable_printer(self, conn=None):
        if not conn:
            conn = self.print_server.open_connection()

        if self.print_server.is_cups:
            conn.enablePrinter(self.id)
        elif self.print_server.is_gcp:
            conn.get('{}/processinvite?accept=true&printerid={}'.format(GCP_BASE_URI, self.id))
