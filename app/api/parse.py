"""Vercel Python entrypoint. Visitors do not need an access code."""
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import sys
import json
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import parse_pdf, parse_csv
from categorise import categorise

class handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        body=json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)

    def do_POST(self):
        if not os.environ.get('GEMINI_API_KEY'):
            self.reply(503,{'error':'The statement reader is not configured on this deployment.'});return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=4*1024*1024:
                self.reply(413,{'error':'Choose a PDF or CSV up to 4 MB for this testing version.'});return
            content=self.rfile.read(size)
            name=self.headers.get('X-File-Name','').lower()
            if name.endswith('.pdf'):tx,warnings=parse_pdf(content)
            elif name.endswith('.csv'):tx,warnings=parse_csv(content)
            else:raise ValueError('Choose a PDF or CSV statement.')
            if not tx:raise ValueError('No transactions were found in this file.')
            warnings.extend(categorise(tx))
            self.reply(200,{'transactions':tx,'warnings':warnings})
        except ValueError as error:
            self.reply(422,{'error':str(error)[:300]})
        except Exception:
            self.reply(503,{'error':'The statement reader could not finish. Please retry shortly.'})
