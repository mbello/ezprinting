# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import json
from .printer import Printer
from .print_server import PrintServer, GCP_BASE_URI

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
        self.gcp_submit_response = None
        self.gcp_submit_response_content = None
        self.gcp_last_message = ""
        self.gcp_last_success = None
        self.state = STATE0_DRAFT

        if not options:
            if self.print_server.is_gcp:
                options = {"version": "1.0", "print": {}}
            elif self.print_server.is_cups:
                options = {}

        self.options = options

    def print(self):
        conn = self.print_server.open_connection()

        if self.print_server.is_cups:
            self.job_id = conn.createJob(self.printer.id, self.title, self.options)
            conn.startDocument(self.printer.id, self.job_id, self.title, self.content_type, 1)
            # Requires pycups >= 1.9.74, lower versions were buggy
            status = conn.writeRequestData(self.content, len(self.content))
            if conn.finishDocument(self.printer.id) == 0:
                self.submitted = True
                self.state = STATE2_QUEUED if status == 100 else STATE0_DRAFT
            return self.submitted

        elif self.print_server.is_gcp:
            # Must NOT set content-type as part of payload below
            payload = \
                {"printerid": self.printer.id,
                 "title": self.title,
                 "ticket": json.dumps(self.options)
                 }
            # Here, the second 'content' could be anything, it is there because
            # requests library requires a 'filename' but we need a filename without
            # extension to not mess up content-type
            files = {'content': ('content', self.content, self.content_type)}
            response = conn.post('{}/submit'.format(GCP_BASE_URI), data=payload, files=files)
            if response.status_code == 200:
                self.submitted = True
                self.gcp_submit_response = response
                self.gcp_submit_response_content = json.loads(response.content, strict=False)
                self.gcp_last_success = self.gcp_submit_response_content["success"]

                if self.gcp_last_success:
                    self.job_id = self.gcp_submit_response_content["job"]["id"]
                    self.state = self.gcp_submit_response_content["job"]["semanticState"]["state"]["type"]
                    self.gcp_last_message = self.gcp_submit_response_content["message"]
            else:
                pass

            return self.gcp_last_success

    @classmethod
    def new_cups(cls, printer_name, content, content_type: str = DEFAULT_CONTENT_TYPE, host: str = "localhost:631",
                 username: str = None, password: str = None, title: str = GENERIC_TITLE, options=None):
        ps = PrintServer.cups(host=host, username=username, password=password)
        p = Printer(print_server=ps, name_or_id=printer_name)
        pj = cls(printer=p, content=content, content_type=content_type, title=title, options=options)
        return pj

    @classmethod
    def new_gcp(cls, service_account: str, printer_id: str, content,
                content_type: str = DEFAULT_CONTENT_TYPE, title: str = GENERIC_TITLE, ticket=None):
        ps = PrintServer.gcp(name="GCP", service_account=service_account)
        p = Printer(ps, printer_id)
        pj = cls(printer=p, content=content, content_type=content_type, title=title, options=ticket)
        return pj
