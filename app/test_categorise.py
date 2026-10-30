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

    def test_grouped_merchants_and_unclear_transfers(self):
        tx = [transaction('2026-10-01', 'Example cafe 123', 1500, 'debit', 0),
              transaction('2026-10-02', 'Example cafe 456', 2500, 'debit', 1),
              transaction('2026-10-02', 'Transfer to Jane', 9000, 'debit', 2)]
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps([{'id':0,'category':'Food & drinks','confidence':.95,'evidence':'example cafe'}])}]}}]}).encode()
        with patch.dict(os.environ, {'GEMINI_API_KEY':'test'}), patch('categorise.urlopen', return_value=Response()) as call:
            self.assertEqual(categorise(tx), [])
            payload = call.call_args[0][0].data.decode()
            self.assertIn('transfer to jane', payload)
            self.assertNotIn('1500', payload)
        self.assertEqual(tx[0]['category'], 'Food & drinks')
        self.assertEqual(tx[1]['category'], 'Food & drinks')
        self.assertTrue(tx[2]['review'])

    def response(self,items):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps(items)}]}}]}).encode()
        return Response()

    def test_transfer_payment_uses_full_narration_and_preserves_recipient(self):
        description='NIBSS transfer '+('routing reference '*30)+'to Fictional Caterer / dinner catering'
        item=transaction('2026-10-01',description,99999,'debit',0)
        self.assertEqual(item['description'],description)
        self.assertEqual(item['type'],'transfer')
        answer=[dict(id=0,category='Food & drinks',confidence=.99,evidence='dinner catering')]
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test'}),patch('categorise.urlopen',return_value=self.response(answer)) as call:
            self.assertEqual(categorise([item]),[])
            payload=call.call_args[0][0].data.decode()
            self.assertIn('fictional caterer / dinner catering',payload)
            self.assertNotIn('99999',payload)
        self.assertEqual(item['description'],description)
        self.assertEqual(item['category'],'Food & drinks')
        self.assertFalse(item['review'])

    def test_invented_evidence_cannot_assign_category(self):
        item=transaction('2026-10-01','Transfer to Fictional Person',100,'debit',0)
        answer=[dict(id=0,category='Food & drinks',confidence=.99,evidence='invented restaurant')]
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test'}),patch('categorise.urlopen',return_value=self.response(answer)):
            categorise([item])
        self.assertEqual(item['type'],'transfer')
        self.assertTrue(item['review'])

    def test_all_description_batches_are_processed(self):
        tx=[transaction('2026-10-01','Unfamiliar merchant '+chr(65+i//26)+chr(65+i%26),100,'debit',i) for i in range(101)]
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test'}),patch('categorise.urlopen',side_effect=[self.response([]),self.response([])]) as call:
            self.assertEqual(categorise(tx),[])
        self.assertEqual(call.call_count,2)

if __name__ == '__main__': unittest.main()
