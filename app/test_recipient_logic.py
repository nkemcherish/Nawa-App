import unittest
from recipient_logic import prepare_recipients,group_repeated_recipients
from server import transaction


class RecipientTests(unittest.TestCase):
    def items(self,count,name='Fictional Recipient',account='1234567890',bank='Kuda'):
        return [transaction('2026-10-01',f'{name}/{account}/{bank} note {i}',100+i,'debit',i) for i in range(count)]
    def apply(self,tx):prepare_recipients(tx);group_repeated_recipients(tx);return tx

    def test_threshold_is_more_than_five(self):
        five=self.apply(self.items(5));self.assertTrue(all('recipientGroup' not in t for t in five))
        six=self.apply(self.items(6));self.assertTrue(all(t['category']=='Fictional Recipient' for t in six))
        self.assertTrue(all(t['categoryKind']=='recipient' and not t['review'] for t in six))

    def test_notes_and_amounts_do_not_split_same_account(self):
        tx=self.apply(self.items(6))
        self.assertEqual(len({t['recipientKey'] for t in tx}),1)
        self.assertEqual(tx[0]['recipientPaymentCount'],6)

    def test_same_name_different_bank_accounts_not_merged(self):
        tx=self.apply(self.items(3)+self.items(3,bank='Opay'))
        self.assertEqual(len({t['recipientKey'] for t in tx}),2)
        self.assertTrue(all('recipientGroup' not in t for t in tx))

    def test_known_food_purpose_is_preserved_in_recipient_group(self):
        tx=self.items(6)
        for t in tx:t.update(type='expense',category='Food & drinks',review=False)
        self.apply(tx)
        self.assertTrue(all(t['category']=='Food & drinks' and t['recipientGroup']=='Fictional Recipient' for t in tx))

    def test_savings_provider_never_counts_as_spending(self):
        tx=self.apply([transaction('2026-10-01','Transfer to PiggyVest',100,'debit',0),transaction('2026-10-01','PiggyVest withdrawal',100,'credit',1)])
        self.assertTrue(all(t['category']=='Savings' and t['type']=='transfer' and not t['review'] for t in tx))
        self.assertEqual(tx[1]['direction'],'credit')

    def test_incoming_money_does_not_trigger_payment_threshold(self):
        tx=self.items(5)+[transaction('2026-10-01','Fictional Recipient/1234567890/Kuda',100,'credit',5)]
        self.apply(tx)
        self.assertTrue(all('recipientGroup' not in t for t in tx))

    def test_personal_name_is_not_assumed_to_be_savings(self):
        tx=self.apply(self.items(6))
        self.assertFalse(any(t.get('internalTransfer') for t in tx))

    def test_plain_transfer_to_name_is_supported(self):
        tx=self.apply([transaction('2026-10-01',f'Transfer to Fictional Person / ref {i}',100,'debit',i) for i in range(6)])
        self.assertTrue(all(t.get('recipientGroup')=='Fictional Person' for t in tx))
