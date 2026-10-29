import json
import os
import unittest
from unittest.mock import patch
from categorise import categorise
from server import transaction

class CategorisationTests(unittest.TestCase):
    def test_already_read_pdf_does_not_call_ai_again(self):
        tx=[transaction('2026-10-01','Unclear seller',100,'debit',0)]
        tx[0]['aiCategoryAttempted']=True
        with patch.dict(os.environ, {'GEMINI_API_KEY':'test'}), patch('categorise.urlopen') as call:
            self.assertEqual(categorise(tx),[])
            call.assert_not_called()

    def test_narration_purpose_overrides_transfer_method(self):
        item=transaction('2026-10-01','NIBSS TRF to seller / fura and nunu',100,'debit',0)
        self.assertEqual(item['category'],'Food & drinks')
        self.assertFalse(item['review'])

    def test_unconfigured_preserves_unknown(self):
        tx = [transaction('2026-10-01', 'Unknown merchant', 1500, 'debit', 0)]
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(categorise(tx))
        self.assertTrue(tx[0]['review'])

    def test_grouped_merchants_and_transfer_exclusion(self):
        tx = [transaction('2026-10-01', 'Example cafe 123', 1500, 'debit', 0),
              transaction('2026-10-02', 'Example cafe 456', 2500, 'debit', 1),
              transaction('2026-10-02', 'Transfer to Jane', 9000, 'debit', 2)]
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps([{'id':0,'category':'Food & drinks','confidence':.95}])}]}}]}).encode()
        with patch.dict(os.environ, {'GEMINI_API_KEY':'test'}), patch('categorise.urlopen', return_value=Response()) as call:
            self.assertEqual(categorise(tx), [])
            payload = call.call_args[0][0].data.decode()
            self.assertNotIn('Jane', payload)
            self.assertNotIn('1500', payload)
        self.assertEqual(tx[0]['category'], 'Food & drinks')
        self.assertEqual(tx[1]['category'], 'Food & drinks')
        self.assertTrue(tx[2]['review'])

if __name__ == '__main__': unittest.main()
