"""Vercel Python entrypoint. Visitors do not need an access code."""
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import sys
import json
import os
import uuid
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import parse_pdf, parse_csv
from categorise import categorise
from processing_budget import processing_budget,ProcessingTimeout

class handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        body=json.dumps(data,allow_nan=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Nawa-Request-Id',getattr(self,'request_id',''))
        self.end_headers();self.wfile.write(body)

    def do_POST(self):
        self.request_id=uuid.uuid4().hex[:12]
        self.stage='upload';self.started=time.monotonic()
        with processing_budget():
            return self._process()

    def _diagnostic(self,error):
        # Never log file names, account details, narrations or model output.
        print(json.dumps({'event':'statement_read_failed','request_id':self.request_id,
                          'stage':self.stage,'error_type':type(error).__name__,
                          'elapsed_seconds':round(time.monotonic()-self.started,1)}),flush=True)

    def _process(self):
        if not os.environ.get('GEMINI_API_KEY'):
            self.reply(503,{'error':'The statement reader is not configured on this deployment.'});return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=4*1024*1024:
                self.reply(413,{'error':'Choose a PDF or CSV up to 4 MB for this testing version.'});return
            content=self.rfile.read(size)
            if len(content)!=size:raise ValueError('The upload was interrupted before the whole file arrived. Please upload it again.')
            name=self.headers.get('X-File-Name','').lower()
            self.stage='extract'
            if name.endswith('.pdf'):tx,warnings=parse_pdf(content)
            elif name.endswith('.csv'):tx,warnings=parse_csv(content)
            else:raise ValueError('Choose a PDF or CSV statement.')
            if not tx:raise ValueError('No transactions were found in this file.')
            self.stage='categorise'
            warnings.extend(categorise(tx))
            self.reply(200,{'transactions':tx,'warnings':warnings})
        except ProcessingTimeout as error:
            self._diagnostic(error)
            self.reply(408,{'error':str(error),'code':'processing_timeout'})
        except ValueError as error:
            self._diagnostic(error)
            self.reply(422,{'error':str(error)[:300]})
        except Exception as error:
            self._diagnostic(error)
            self.reply(503,{'error':'The statement reader could not finish. Please retry shortly.'})
