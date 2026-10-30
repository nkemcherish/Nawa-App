"""Nawa local-first demo server. Statement files are parsed in memory and not stored."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from io import BytesIO
import json, re, csv, os
from decimal import Decimal, InvalidOperation
from datetime import datetime
from urllib.parse import urlparse
from categorise import categorise

ROOT=Path(__file__).resolve().parent
MAX_FILE=12*1024*1024
DATE_RE=re.compile(r'(?<!\d)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{1,2}-\d{1,2})(?!\d)')
MONEY_RE=re.compile(r'(?<![\w])(?:[-+]?\s*₦?\s*\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|[-+]?\s*₦?\s*\d+(?:\.\d{1,2})?)(?!\w)')

def money(s):
    s=str(s or '').replace('₦','').replace('NGN','').replace(',','').strip()
    if not s or s in ('-','—'): return None
    s=re.sub(r'\s+', '',s)
    if s.startswith('(') and s.endswith(')'): s='-'+s[1:-1]
    try:return float(Decimal(s))
    except (InvalidOperation,ValueError):return None

def date_normal(s):
    s=str(s).strip()
    for fmt in ('%d/%m/%Y','%d-%m-%Y','%Y-%m-%d','%d/%m/%y','%d-%m-%y','%m/%d/%Y','%m-%d-%Y'):
        try:return datetime.strptime(s,fmt).strftime('%Y-%m-%d')
        except ValueError: pass
    return None

def transaction(date,description,amount,direction,idx):
    typ='income' if direction=='credit' else 'unknown'
    desc=description.strip()[:240]
    lower=desc.lower()
    cat='Uncategorised'
    if direction=='debit':
        typ='transfer' if any(w in lower for w in ('transfer','trf','sent to','nibss')) else 'expense'
        rules=[('Food & drinks',('restaurant','chicken','food','grocery','supermarket','shoprite','eatery','fura','nunu','suya','amala','jollof','shawarma','bakery','pizza')),('Transport',('uber','bolt','fuel','transport','ride')),('Bills & utilities',('electric','power','airtime','data bundle','dstv','internet')),('Subscriptions',('netflix','spotify','subscription')),('Shopping',('shopping','jumia','amazon')),('Housing',('rent','landlord'))]
        for category,words in rules:
            if any(re.search(r'\b'+re.escape(w)+r'\b',lower) for w in words): cat=category;typ='expense';break
        if typ=='transfer':cat='Transfers'
    elif direction=='credit':cat='Money received'
    return {'id':f'imp-{idx}','date':date,'description':desc,'amount':round(abs(amount),2),'type':typ,'category':cat,'review':cat=='Uncategorised' or typ=='transfer'}

def parse_csv(content):
    text=content.decode('utf-8-sig',errors='replace')
    reader=csv.DictReader(text.splitlines())
    if not reader.fieldnames:raise ValueError('No column headings were found in the CSV.')
    fields={re.sub(r'[^a-z]','',str(f).lower()):f for f in reader.fieldnames}
    def col(*names):
        for name in names:
            if name in fields:return fields[name]
        return None
    dc=col('date','transactiondate','valuedate','posteddate'); ds=col('description','narration','details','remarks','transactiondetails'); debit=col('debit','withdrawal','withdrawals','dr');credit=col('credit','deposit','deposits','cr');amt=col('amount','transactionamount')
    if not dc or not ds or not ((debit or credit) or amt):raise ValueError('The CSV needs date, description, and debit/credit or amount columns.')
    tx=[];skipped=0
    for i,row in enumerate(reader):
        d=date_normal(row.get(dc,''));desc=(row.get(ds,'') or '').strip()
        if not d or not desc:skipped+=1;continue
        deb=money(row.get(debit)) if debit else None;cred=money(row.get(credit)) if credit else None
        if (deb or 0)>0:tx.append(transaction(d,desc,deb,'debit',i));continue
        if (cred or 0)>0:tx.append(transaction(d,desc,cred,'credit',i));continue
        a=money(row.get(amt)) if amt else None
        if a is not None and a!=0:tx.append(transaction(d,desc,a,'credit' if a>0 else 'debit',i))
        else:skipped+=1
    return tx,[f'{skipped} rows were skipped because they could not be parsed.'] if skipped else []

def parse_pdf_local(content):
    import pdfplumber
    transactions=[]; warnings=[]; row_counter=0
    with pdfplumber.open(BytesIO(content)) as pdf:
        if len(pdf.pages)>65:raise ValueError('This PDF has too many pages for the current local parser (maximum 65).')
        for page_no,page in enumerate(pdf.pages,1):
            tables=page.extract_tables() or []
            used=False
            for tbl in tables:
                if not tbl or len(tbl)<2:continue
                hdridx=None
                for ix,row in enumerate(tbl[:5]):
                    headings=[re.sub(r'[^a-z]','',(c or '').lower()) for c in row]
                    if any('date' in h for h in headings) and any('debit' in h or 'withdraw' in h for h in headings) and any('credit' in h or 'deposit' in h for h in headings):hdridx=ix;break
                if hdridx is None:continue
                h=[re.sub(r'[^a-z]','',(c or '').lower()) for c in tbl[hdridx]]
                def find(words):return next((i for i,t in enumerate(h) if any(w in t for w in words)),None)
                di=find(('date',)); ni=find(('narration','description','details','remarks'));dr=find(('debit','withdraw'));cr=find(('credit','deposit'))
                if di is None or dr is None or cr is None:continue
                for row in tbl[hdridx+1:]:
                    if not row:continue
                    def cell(i):return (row[i] or '').replace('\n',' ') if i is not None and i<len(row) else ''
                    d=date_normal(cell(di));description=cell(ni) or 'Bank transaction';deb=money(cell(dr));cred=money(cell(cr))
                    if d and ((deb or 0)>0 or (cred or 0)>0):
                        transactions.append(transaction(d,description,deb if (deb or 0)>0 else cred,'debit' if (deb or 0)>0 else 'credit',row_counter));row_counter+=1;used=True
            if used:continue
            text=page.extract_text(layout=False) or ''
            if not text.strip(): warnings.append(f'Page {page_no} contains no extractable text; scanned statements need OCR.');continue
            for line in text.splitlines():
                match=DATE_RE.search(line)
                if not match or match.start()>5:continue
                d=date_normal(match.group(1))
                if not d:continue
                rest=line[match.end():].strip()
                # Conservative fallback: only interpret columns if TWO labelled debit/credit/balance values are visibly present.
                # Otherwise skip; guessing debit/credit from an unlabeled number could reverse cash flow.
                hits=list(re.finditer(r'(?<!\S)(?:₦?\s*\d[\d,]*\.\d{2}|[-—])(?=\s|$)',rest))
                if len(hits)<3:continue
                trailing=hits[-3:]
                description=rest[:trailing[0].start()].strip()
                if not description:continue
                deb=money(trailing[0].group());cred=money(trailing[1].group())
                if (deb or 0)>0 and not (cred or 0)>0:transactions.append(transaction(d,description,deb,'debit',row_counter));row_counter+=1
                elif (cred or 0)>0 and not (deb or 0)>0:transactions.append(transaction(d,description,cred,'credit',row_counter));row_counter+=1
    warnings.append('PDF layouts differ by bank. Review every extracted entry against your statement before trusting totals.')
    return transactions,warnings

def parse_pdf(content):
    if not content.startswith(b'%PDF'):
        raise ValueError('Please choose a valid PDF statement.')
    if len(content)>MAX_FILE:
        raise ValueError('Choose a statement smaller than 12 MB.')
    if os.environ.get('GEMINI_API_KEY'):
        from statement_ai import read_pdf_report
        rows,warnings=read_pdf_report(content)
        tx=[]
        for i,row in enumerate(rows):
            d,desc,amount,direction=row[:4]
            item=transaction(d,desc,amount,direction,i)
            item['aiCategoryAttempted']=row[4].get('category_attempted',True) if len(row)>4 else True
            category=row[4].get('category') if len(row)>4 else None
            if direction=='debit' and category:
                item.update(type='expense',category=category,review=False,classifiedBy='gemini')
            tx.append(item)
        return tx,warnings
    return parse_pdf_local(content)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def do_POST(self):
        if urlparse(self.path).path!='/api/parse':self.send_error(404);return
        size=int(self.headers.get('Content-Length','0'))
        if size<1 or size>MAX_FILE:self._json(413,{'error':'File must be smaller than 12 MB.'});return
        content=self.rfile.read(size)
        filename=self.headers.get('X-File-Name','').lower()
        try:
            if filename.endswith('.csv'):tx,warnings=parse_csv(content)
            elif filename.endswith('.pdf') and content.startswith(b'%PDF'):tx,warnings=parse_pdf(content)
            else:raise ValueError('Please choose a valid PDF or CSV statement.')
            if not tx:raise ValueError('No reliable transactions could be extracted from this file. This bank layout may not be supported yet. No report was generated.')
            warnings.extend(categorise(tx))
            self._json(200,{'transactions':tx,'warnings':warnings,'count':len(tx)})
        except Exception as exc:self._json(422,{'error':str(exc)[:300]})
    def _json(self,code,data):
        body=json.dumps(data).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
if __name__=='__main__':
    host=os.environ.get('NAWA_HOST','127.0.0.1');port=int(os.environ.get('PORT','8765'))
    print(f'Nawa running on http://{host}:{port}',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
