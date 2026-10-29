import importlib.util
import unittest
from pathlib import Path
from io import BytesIO
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('vercel_parse',Path(__file__).parent/'api'/'parse.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)

class VercelTests(unittest.TestCase):
    def request(self,headers=None,body=b'%PDF synthetic'):
        instance=object.__new__(api.handler)
        instance.headers={'X-File-Name':'test.pdf','Content-Length':str(len(body)),**(headers or {})}
        instance.rfile=BytesIO(body);result=[]
        instance.reply=lambda code,data:result.append((code,data))
        instance.do_POST();return result[0]

    def test_missing_server_key(self):
        with patch.dict(api.os.environ,{},clear=True):self.assertEqual(self.request()[0],503)

    def test_upload_without_tester_code(self):
        with patch.dict(api.os.environ,{'GEMINI_API_KEY':'fake'},clear=True),patch.object(api,'parse_pdf',return_value=([{'id':'test'}],[])),patch.object(api,'categorise',return_value=[]):
            self.assertEqual(self.request()[0],200)

    def test_success_and_upload_limit(self):
        with patch.dict(api.os.environ,{'GEMINI_API_KEY':'fake'},clear=True),patch.object(api,'parse_pdf',return_value=([{'id':'test'}],[])),patch.object(api,'categorise',return_value=[]):
            self.assertEqual(self.request()[0],200)
            self.assertEqual(self.request({'Content-Length':str(5*1024*1024)})[0],413)

    def test_meaningful_reader_error(self):
        with patch.dict(api.os.environ,{'GEMINI_API_KEY':'fake'},clear=True),patch.object(api,'parse_pdf',side_effect=ValueError('This PDF is locked.')):
            code,data=self.request()
            self.assertEqual(code,422);self.assertEqual(data['error'],'This PDF is locked.')

if __name__=='__main__':unittest.main()
