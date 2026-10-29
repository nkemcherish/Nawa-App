import unittest
from statement_ai import validate_rows, reconcile, read_pdf_report, read_chunk
from urllib.error import HTTPError
from io import BytesIO
from pypdf import PdfWriter
from unittest.mock import patch

class ValidationTests(unittest.TestCase):
    def row(self, **changes):
        return dict(date='2026-10-01', description='Synthetic cafe', amount=1200.50, direction='debit', confidence=.99, **changes)
    def test_valid_duplicates_preserved(self):
        row=self.row()
        self.assertEqual(len(validate_rows({'complete':True,'transactions':[row,row]})),2)
    def test_reject_incomplete(self):
        with self.assertRaises(ValueError): validate_rows({'complete':False,'transactions':[self.row()]})
    def test_reject_bad_values(self):
        for key,value in [('amount',-1),('amount','NaN'),('amount',1.001),('direction','unknown'),('date','2026-02-30'),('confidence',.4)]:
            row=self.row();row[key]=value
            with self.assertRaises(ValueError): validate_rows({'complete':True,'transactions':[row]})

    def test_reconcile_totals(self):
        result={'complete':True,'transactions':[self.row()], 'opening_balance':2000,'closing_balance':799.50,'total_debits':1200.50,'total_credits':0,'transaction_count':1,'currency':'NGN'}
        self.assertTrue(reconcile(result)[1])
        result['closing_balance']=800
        with self.assertRaises(ValueError): reconcile(result)

    def test_reject_missing_row_and_other_currency(self):
        for extra in [{'transaction_count':2},{'currency':'USD'},{'total_debits':500}]:
            with self.assertRaises(ValueError): reconcile(dict(complete=True,transactions=[self.row()],**extra))

    def test_reverse_running_balances(self):
        older=self.row();older['balance']=8799.50
        newer=self.row();newer['amount']=100;newer['balance']=8699.50
        self.assertIn('running balances',reconcile({'complete':True,'transactions':[newer,older]})[1])
        newer['balance']=8000
        with self.assertRaises(ValueError): reconcile({'complete':True,'transactions':[older,newer]})

    def test_encrypted_and_damaged_pdf(self):
        writer=PdfWriter();writer.add_blank_page(width=200,height=200);writer.encrypt('secret');buffer=BytesIO();writer.write(buffer)
        with self.assertRaisesRegex(ValueError,'password'): read_pdf_report(buffer.getvalue())
        with self.assertRaisesRegex(ValueError,'damaged'): read_pdf_report(b'not a PDF')

    def test_all_pages_and_chunk_boundary(self):
        writer=PdfWriter()
        for _ in range(5):writer.add_blank_page(width=200,height=200)
        buffer=BytesIO();writer.write(buffer)
        a=self.row();a['balance']=8799.50
        b=self.row();b['amount']=100;b['balance']=8699.50
        chunks=[{'complete':True,'page_count':4,'transactions':[a]}, {'complete':True,'page_count':1,'transactions':[b]}]
        with patch('statement_ai.read_chunk',side_effect=chunks) as call:
            rows,warnings=read_pdf_report(buffer.getvalue())
            self.assertEqual(len(rows),2);self.assertEqual(call.call_count,2)
            self.assertIn('running balances',warnings[0])

    def test_description_category_and_evidence(self):
        writer=PdfWriter();writer.add_blank_page(width=200,height=200);buffer=BytesIO();writer.write(buffer)
        for evidence,expected in [('fura','Food & drinks'),('invented evidence',None)]:
            row=self.row();row.update(description='NIBSS transfer to seller / fura and nunu',category='Food & drinks',category_confidence=.99,category_evidence=evidence)
            with patch('statement_ai.read_chunk',return_value={'complete':True,'page_count':1,'transactions':[row]}):
                rows,_=read_pdf_report(buffer.getvalue())
                self.assertEqual(rows[0][4]['category'],expected)

    def test_temporary_service_failure_retries(self):
        expected={'complete':True,'transactions':[self.row()]}
        transient=HTTPError('https://example.invalid',503,'unavailable',{},None)
        with patch('statement_ai.read_chunk_once',side_effect=[transient,expected]) as call,patch('statement_ai.time.sleep'):
            self.assertEqual(read_chunk(b'pdf'),expected)
            self.assertEqual(call.call_count,2)

    def test_incomplete_response_retries(self):
        expected={'complete':True,'transactions':[self.row()]}
        with patch('statement_ai.read_chunk_once',side_effect=[ValueError('incomplete'),expected]) as call,patch('statement_ai.time.sleep'):
            self.assertEqual(read_chunk(b'pdf'),expected)
            self.assertEqual(call.call_count,2)

    def test_persistent_timeout_is_not_called_bad_pdf(self):
        with patch('statement_ai.read_chunk_once',side_effect=TimeoutError()),patch('statement_ai.time.sleep'):
            with self.assertRaisesRegex(ValueError,'timed out'):read_chunk(b'pdf')

if __name__=='__main__': unittest.main()
