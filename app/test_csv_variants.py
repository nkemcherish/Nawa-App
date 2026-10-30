import unittest
from server import parse_csv


class CsvVariantTests(unittest.TestCase):
    def test_money_in_out_labels(self):
        tx,_=parse_csv(b'Date,Narration,Money In,Money Out\n01 Oct 2026,Transfer groceries,,100\n02 Oct 2026,Salary,500,\n')
        self.assertEqual([t['type'] for t in tx],['expense','income'])

    def test_explicit_direction_overrides_unsigned_amount(self):
        tx,_=parse_csv(b'Date,Description,Amount,Type\n01/10/2026,Groceries,100,Debit\n02/10/2026,Salary,500,Credit\n')
        self.assertEqual([t['type'] for t in tx],['expense','income'])

    def test_nonfinite_amounts_never_enter_report_json(self):
        tx,warnings=parse_csv(b'Date,Description,Amount\n01/10/2026,Invalid,NaN\n02/10/2026,Invalid,Infinity\n')
        self.assertEqual(tx,[])
        self.assertIn('2 rows',warnings[0])
