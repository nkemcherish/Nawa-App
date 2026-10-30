"""Fictional PDFs model documented column structures; no customer data."""
import unittest
from io import BytesIO
from unittest.mock import patch
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from statement_layout import read_labelled_pdf, document_context, context_hint, table_hint, source_summary, amount, header_rows, researched_guidance
from statement_ai import read_pdf_report, reconcile


def fixture(headings=None, bad_balance=False, grouped=False, pages=1, currency='NGN', omit_second_date=False):
    out=BytesIO();c=Canvas(out,pagesize=(650,842));c.setFont('Helvetica',9)
    c.drawString(22,810,'Fictional test statement '+currency)
    c.drawString(22,790,'Statement Period: 01/09/2026 - 31/10/2026')
    for y,label,value in [(770,'Opening Balance','1,000.00'),(750,'Closing Balance','1,100.00'),
                          (730,'Total Debits','100.00'),(710,'Total Credits','200.00')]:
        c.drawString(22,y,label+': '+currency+' '+value)
    cols=headings or [(22,'Trans Date'),(115,'Description'),(320,'Debit'),(410,'Credit'),(510,'Balance')]
    if grouped:
        cols=[(22,'September 30th'),(115,'Money In'),(210,'Money Out'),(305,'Category'),(390,'Destination'),(510,'Description'),(590,'Balance')]
    for x,label in cols: c.drawString(x,680,label)
    def draw(y,values):
        for (x,_),value in zip(cols,values): c.drawString(x,y,value)
    if grouped:
        draw(650,['12:00:01','','100.00','purchase','Fictional shop','Groceries','900.00'])
    else:
        values={'date':'30/09/2026','description':'Fictional shop','debit':'100.00','credit':'--','balance':'900.00','value':'01/10/2026','ref':'TEST-1'}
        for x,label in cols:
            role=('value' if 'Value' in label else 'ref' if 'Ref' in label else 'date' if 'Date' in label else
                  'debit' if any(t in label for t in ('Debit','Withdrawal','DR','Money Out')) else
                  'credit' if any(t in label for t in ('Credit','Deposit','CR','Money In')) else
                  'balance' if 'Balance' in label else 'description')
            c.drawString(x,650,values[role])
    if pages>1:
        # Continue the same grouped day across a page boundary without a heading.
        for _ in range(pages-1):
            c.showPage();c.setFont('Helvetica',9)
        for x,label in cols:
            if not grouped or x!=22: c.drawString(x,790,label)
        y=760
    else: y=610
    if grouped:
        draw(y,['12:10:00','200.00','','transfer','Fictional employer','Salary','1,100.00' if not bad_balance else '1,050.00'])
    else:
        for x,label in cols:
            value=(('' if omit_second_date else '01/10/2026') if 'Date' in label else 'TEST-2' if 'Ref' in label else
                   '--' if any(t in label for t in ('Debit','Withdrawal','DR','Money Out')) else
                   '200.00' if any(t in label for t in ('Credit','Deposit','CR','Money In')) else
                   ('1,050.00' if bad_balance else '1,100.00') if 'Balance' in label else 'Fictional salary')
            c.drawString(x,y,value)
    c.save();return out.getvalue()


class LayoutTests(unittest.TestCase):
    def read(self,content): return read_labelled_pdf(content,PdfReader(BytesIO(content)))

    def test_labelled_column_families(self):
        families=[
            [(22,'Trans Date'),(115,'Description'),(320,'Debit'),(410,'Credit'),(510,'Balance')],
            [(22,'Date'),(115,'Narration'),(320,'Credit'),(410,'Debit'),(510,'Balance')],
            [(22,'Trans Date'),(100,'Ref. Number'),(180,'Transaction Details'),(330,'Value Date'),(420,'Withdrawal(DR)'),(510,'Deposit(CR)'),(590,'Balance')],
            [(22,'Trans Date'),(115,'Description'),(320,'Debit'),(400,'Credit'),(470,'Value Date'),(560,'Balance')],
            [(22,'Date'),(115,'Remarks'),(320,'Money In'),(410,'Money Out'),(510,'Balance')],
        ]
        for columns in families:
            with self.subTest(columns=columns):
                result=self.read(fixture(columns))
                self.assertIsNotNone(result)
                rows,checks=reconcile(result)
                self.assertEqual([r[3] for r in rows],['debit','credit'])
                self.assertIn('opening and closing balances',checks)
                self.assertIn('running balances',checks)

    def test_grouped_days_continue_across_pages(self):
        result=self.read(fixture(grouped=True,pages=2))
        self.assertIsNotNone(result)
        self.assertEqual([r['date'] for r in result['transactions']],['2026-09-30']*2)
        reconcile(result)

    def test_blank_transaction_date_inherits_printed_date(self):
        result=self.read(fixture(omit_second_date=True))
        self.assertIsNotNone(result)
        self.assertEqual([r['date'] for r in result['transactions']],['2026-09-30']*2)
        reconcile(result)

    def test_wrapped_headers_combine_semantics_and_position(self):
        def word(text,x,y): return dict(text=text,x0=x,top=y)
        rows=[[word('Transaction',22,10),word('Transaction',115,10),word('Money',320,10),word('Money',410,10),word('Balance',510,10)],
              [word('Date',22,20),word('Particulars',115,20),word('Out',320,20),word('In',410,20)]]
        cols,span=header_rows(rows,0)
        self.assertEqual(span,2)
        self.assertEqual([r for _,r in cols],['date','description','debit','credit','balance'])

    def test_researched_rules_depend_on_structure_not_bank_mentions(self):
        row=[dict(text=t) for t in 'Trans. Time Value Date Description Debit Credit Balance Channel Transaction Reference'.split()]
        self.assertIn('above AND below',researched_guidance(row))
        self.assertEqual(researched_guidance([dict(text='Sent from OPay to Kuda')]),'')

    def test_header_merge_never_swallows_transaction_amount(self):
        rows=[[dict(text='Money',x0=100,top=10)],
              [dict(text='100.00',x0=100,top=20)]]
        self.assertIsNone(header_rows(rows,0)[0])

    def test_verified_local_read_avoids_ai_extraction(self):
        with patch('statement_ai.read_chunk') as ai:
            rows,warnings=read_pdf_report(fixture())
        ai.assert_not_called()
        self.assertEqual(len(rows),2)
        self.assertFalse(rows[0][4]['category_attempted'])
        self.assertIn('labelled PDF columns',warnings[0])

    def test_local_mismatch_falls_back_without_returning_partial_report(self):
        with patch('statement_ai.read_chunk',side_effect=ValueError('AI unavailable')) as ai:
            with self.assertRaisesRegex(ValueError,'AI unavailable'):
                read_pdf_report(fixture(bad_balance=True))
        ai.assert_called_once()

    def test_foreign_currency_not_accepted_locally(self):
        self.assertIsNone(self.read(fixture(currency='USD')))

    def test_context_carries_day_and_period_into_page_group(self):
        content=fixture(grouped=True,pages=2)
        contexts=document_context(PdfReader(BytesIO(content)))
        hint=context_hint(contexts[1])
        self.assertIn('2026-09-01 to 2026-10-31',hint)
        self.assertIn('month 9, day 30',hint)

    def test_column_context_contains_structure_without_personal_data(self):
        hint=table_hint(fixture(grouped=True))
        self.assertIn('credit:',hint)
        self.assertIn('debit:',hint)
        self.assertNotIn('Fictional employer',hint)
        self.assertNotIn('1,000',hint)

    def test_summary_is_read_from_source_not_ai(self):
        summary=source_summary(fixture())
        self.assertEqual(summary['opening_balance'],'1000.00')
        self.assertEqual(summary['closing_balance'],'1100.00')
        self.assertEqual(summary['total_debits'],'100.00')

    def test_ai_fallback_receives_document_context(self):
        with patch('statement_ai.read_chunk',side_effect=ValueError('AI unavailable')) as ai:
            with self.assertRaisesRegex(ValueError,'AI unavailable'):
                read_pdf_report(fixture(grouped=True,bad_balance=True))
        feedback=ai.call_args.kwargs['feedback']
        self.assertIn('2026-09-01 to 2026-10-31',feedback)
        self.assertIn('credit:',feedback)

    def test_long_ai_read_checks_full_statement_summary(self):
        content=fixture(grouped=True,pages=5)
        # A missed first debit leaves a plausible isolated credit, but cannot
        # match the source summary. No partial report may be returned.
        row=dict(date='2026-09-30',description='Fictional salary',amount=200,
                 direction='credit',balance=1100,confidence=.99)
        chunks=[dict(complete=True,page_count=4,transactions=[]),
                dict(complete=True,page_count=1,transactions=[row])]
        with patch('statement_ai.read_chunk',side_effect=chunks):
            with self.assertRaisesRegex(ValueError,'printed statement totals'):
                read_pdf_report(content)

    def test_text_engine_failure_keeps_visual_fallback_available(self):
        row=dict(date='2026-09-30',description='Fictional shop',amount=100,direction='debit',confidence=.99)
        result=dict(complete=True,page_count=1,transactions=[row])
        with (patch('statement_ai.read_labelled_pdf',side_effect=RuntimeError('text engine')),
             patch('statement_ai.document_context',side_effect=RuntimeError('text engine')),
             patch('statement_ai.table_hint',side_effect=RuntimeError('text engine')),
             patch('statement_ai.source_summary',side_effect=RuntimeError('text engine')),
             patch('statement_ai.read_chunk',return_value=result)):
            rows,_=read_pdf_report(fixture())
        self.assertEqual(len(rows),1)

    def wallet_fixture(self, *, count=1, total='100.00', savings=False):
        out=BytesIO();c=Canvas(out,pagesize=(612,792));c.setFont('Helvetica',6)
        c.drawString(60,740,'Fictional Wallet Account NGN')
        for y,labels,values in [(680,['Opening Balance','Total Debit','Debit Count'],['1,000.00',total,str(count)]),
                               (640,['Closing Balance','Total Credit','Credit Count'],['1,100.00','200.00','1'])]:
            for x,label,value in zip([60,224,383],labels,values):
                c.drawString(x,y,label);c.drawString(x,y-15,value)
        c.drawString(378,580,'Balance')
        headings=[(71,'Trans. Time'),(131,'Value Date'),(178,'Description'),(304,'Debit(NGN)'),
                  (342,'Credit(NGN)'),(378,'After(NGN)'),(422,'Channel'),(478,'Transaction Reference')]
        c.setFont('Helvetica',4.5)
        for x,label in headings:c.drawString(x,568,label)
        def tx(y,direction,balance,description):
            c.drawString(71,y,'01 Oct 2026 12:00:00');c.drawString(131,y,'01 Oct 2026')
            c.drawString(304,y,'100.00' if direction=='debit' else '--')
            c.drawString(342,y,'200.00' if direction=='credit' else '--')
            c.drawString(378,y,balance)
            c.drawString(178,y+9,description);c.drawString(178,y-8,'Fictional narration continuation')
        tx(540,'debit','850.00','Fictional cafe')
        c.showPage();c.setFont('Helvetica',4.5)
        if savings:c.drawString(60,750,'Savings Account')
        # No repeated table header on continuation pages.
        tx(700,'credit','1,100.00','Fictional salary')
        c.save();return out.getvalue()

    def test_wallet_counts_and_totals_can_verify_nonsequential_balances(self):
        with patch('statement_ai.read_chunk') as ai:
            rows,warnings=read_pdf_report(self.wallet_fixture())
        ai.assert_not_called()
        self.assertEqual(len(rows),2)
        self.assertIn('Fictional cafe',rows[0][1])
        self.assertIn('Fictional salary',rows[1][1])
        self.assertNotIn('salary',rows[0][1])
        self.assertTrue(any('Individual running balances' in w for w in warnings))
        self.assertTrue(any('transaction count' in w for w in warnings))

    def test_wallet_invalid_counts_totals_or_savings_never_bypass_checks(self):
        for kwargs in (dict(count=2),dict(total='101.00'),dict(savings=True)):
            with self.subTest(kwargs=kwargs),patch('statement_ai.read_chunk',side_effect=ValueError('fallback')) as ai:
                with self.assertRaisesRegex(ValueError,'fallback'):
                    read_pdf_report(self.wallet_fixture(**kwargs))
                ai.assert_called_once()

    def test_missing_dates_are_not_guessed(self):
        content=fixture(grouped=True).replace(b'01/09/2026',b'xx/xx/xxxx')
        # Reportlab compresses streams, so use a reader stub with missing metadata.
        class Page:
            def extract_text(self): return 'Kuda NGN Statement'
        class Reader: pages=[Page()]
        self.assertIsNone(read_labelled_pdf(content,Reader()))

    def test_money_suffix_and_ambiguous_numbers(self):
        self.assertEqual(amount('1,200.50 DR'),-1200.50)
        for value in ('1.000,50','NaN','1,234','1.234'):
            with self.assertRaises(ValueError): amount(value)


if __name__=='__main__': unittest.main()
