"""Recipient identity, savings destinations and repeated outgoing payment groups."""
import hashlib
import re
import unicodedata
from collections import defaultdict


def normalise(value):
    text=unicodedata.normalize('NFKC',value).casefold()
    return re.sub(r'[^\w]+',' ',text).strip()


def recipient_from_description(description):
    # Prefer explicit account structure or transfer-to markers, never arbitrary
    # narration words. Different account numbers are different recipients.
    account=re.search(r'([^/|]+?)\s*/\s*(\d{10})\s*/\s*([^/|\n]*)',description)
    if account:
        name,number,bank=account.groups()
        name=re.sub(r'^.*?\b(?:transfer\s+to|sent\s+to|payment\s+to|trf\s+to)\s*','',name,flags=re.I)
        name=re.sub(r'^POS\s+Transfer\s*[-:]\s*','',name,flags=re.I)
        return name.strip(' -:'),number,bank.strip()
    named=re.search(r'\b(?:transfer\s+to|sent\s+to|payment\s+to|trf\s+to)\s*[:\-]?\s*([^/|\n]+)',description,re.I)
    if named:
        name=re.split(r'\s+(?:for|ref|reference|on)\b|\s*[-–]\s*(?:OPAY|KUDA|PALMPAY|GTBANK|ACCESS|ZENITH)\b|\d{8,}',named.group(1),maxsplit=1,flags=re.I)[0]
        return name.strip(' -:'),'',''
    return None


def prepare_recipients(transactions):
    for t in transactions:
        description=t.get('description','')
        found=recipient_from_description(description)
        if found:
            name,account,bank=found
            if 2<=len(name)<=100 and re.search(r'[A-Za-z]',name):
                bank_match=re.search(r'\b(?:opay|palmpay|kuda|sterling|gtbank|guaranty|access|zenith|moniepoint|fcmb|fidelity|ecobank|stanbic|wema|first\s*bank|uba|union|unity|polaris|providus|globus|keystone)\b',bank,re.I)
                bank_key=normalise(bank_match.group()) if bank_match else ''
                identity='account:'+bank_key+':'+account if account else 'name:'+normalise(name)
                t.update(recipientName=name,recipientKey=hashlib.sha256(identity.encode()).hexdigest()[:20])
                if account:t['recipientAccountSuffix']=account[-4:]
        # Savings providers are explicit destinations. A repeated personal name
        # alone is never evidence that this is the user's own account.
        if t.get('internalTransfer') or re.search(r'\bpiggy\s*vest\b',description,re.I):
            t.update(type='transfer',category='Savings',review=False,internalTransfer=True,savingsTransfer=True)


def group_repeated_recipients(transactions):
    groups=defaultdict(list)
    for t in transactions:
        if t.get('recipientKey') and t.get('direction')!='credit' and t.get('type') not in ('income','refund'):
            groups[t['recipientKey']].append(t)
    labels=defaultdict(list)
    for key,items in groups.items():
        if len(items)>5:labels[normalise(items[0]['recipientName'])].append(key)
    for key,items in groups.items():
        if len(items)<=5:continue
        name=items[0]['recipientName']
        if normalise(name) in {'food drinks','transport','bills utilities','housing','shopping','subscriptions','health','family support','other spending','savings','transfers','money received','uncategorised'}:
            name='Payments to '+name
        if len(labels[normalise(name)])>1:name+=' · '+items[0].get('recipientAccountSuffix',key[:4])
        for t in items:
            t.update(recipientGroup=name,recipientPaymentCount=len(items))
            # Keep already established purposes. An unresolved payment can be
            # named by recipient without inventing what it bought.
            if not t.get('internalTransfer') and t.get('review'):
                t.update(type='expense',category=name,categoryKind='recipient',review=False,
                         categoryEvidence=f'{len(items)} outgoing payments to this recipient; purpose unconfirmed')
