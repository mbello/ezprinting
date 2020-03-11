from ezprinting.printer import Printer
from ezprinting.print_server import PrintServer

STATE0_DRAFT = "DRAFT"
STATE1_HELD = "HELD"
STATE2_QUEUED = "QUEUED"
STATE3_IN_PROGRESS = "IN_PROGRESS"
STATE4_STOPPED = "STOPPED"
STATE5_DONE = "DONE"
STATE6_ABORTED = "ABORTED"

GENERIC_TITLE = "A print job"
DEFAULT_CONTENT_TYPE = 'application/pdf'


class PrintJob:
    def __init__(self, printer: Printer, content, content_type: str = DEFAULT_CONTENT_TYPE, title: str = GENERIC_TITLE,
                 options=None):
        self.printer = printer
        self.print_server = self.printer.print_server
        self.content = content
        self.content_type = content_type
        self.title = title
        self.job_id = None
        self.submitted = False
        self.state = STATE0_DRAFT
        self.options = options or {}

    def print(self):
        conn = self.print_server.open_connection()

        self.job_id = conn.createJob(self.printer.id, self.title, self.options)
        conn.startDocument(self.printer.id, self.job_id, self.title, self.content_type, 1)
        # Requires pycups >= 1.9.74, lower versions were buggy
        status = conn.writeRequestData(self.content, len(self.content))
        if conn.finishDocument(self.printer.id) == 0:
            self.submitted = True
            self.state = STATE2_QUEUED if status == 100 else STATE0_DRAFT
        return self.submitted

    @classmethod
    def new_cups(cls, printer_name, content, content_type: str = DEFAULT_CONTENT_TYPE, host: str = "localhost:631",
                 username: str = None, password: str = None, title: str = GENERIC_TITLE, options=None):
        ps = PrintServer.cups(host=host, username=username, password=password)
        p = Printer(print_server=ps, name_or_id=printer_name)
        pj = cls(printer=p, content=content, content_type=content_type, title=title, options=options)
        return pj
