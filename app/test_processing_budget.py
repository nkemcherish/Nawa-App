import unittest
from unittest.mock import patch
from processing_budget import processing_budget,check_budget,io_timeout,ProcessingTimeout


class BudgetTests(unittest.TestCase):
    def test_network_timeout_cannot_exceed_remaining_budget(self):
        with patch('processing_budget.time.monotonic',return_value=100):
            with processing_budget(20):
                self.assertEqual(io_timeout(100),15)

    def test_expired_budget_and_context_reset(self):
        with patch('processing_budget.time.monotonic',return_value=100):
            with processing_budget(3):
                with self.assertRaises(ProcessingTimeout):check_budget()
        self.assertIsNone(check_budget())

    def test_category_timeout_keeps_parsed_transactions(self):
        import os
        from categorise import categorise
        tx=[dict(type='transfer',review=True,description='Transfer to Fictional Person')]
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test'}),processing_budget(10),patch('categorise.urlopen') as api:
            warnings=categorise(tx)
        api.assert_not_called()
        self.assertIn('transactions were read',warnings[0])
