import json
import cups
from ezprinting.print_server import PrintServer


class Printer:
    def __init__(self, print_server: PrintServer, name_or_id: str):
        self.print_server = print_server
        self.id = name_or_id

    def check_printer_exists(self, conn=None):
        if not conn:
            conn = self.print_server.open_connection()

        try:
            p = self.get_printer_attributes(conn=conn)
            return True if p['printer-name'] == self.id else False
        except cups.IPPError:
            return False

    def get_printer_attributes(self, conn=None):
        if not conn:
            conn = self.print_server.open_connection()
        
        return conn.getPrinterAttributes(self.id)

    def enable_printer(self, conn=None):
        if not conn:
            conn = self.print_server.open_connection()

        conn.enablePrinter(self.id)
