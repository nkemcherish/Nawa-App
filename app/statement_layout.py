"""Source-driven PDF table reading. Unsupported/ambiguous layouts fall back to AI.

No account identifiers or document text are persisted. Column positions come from
the uploaded header, rather than a bank name or fixed page coordinates.
"""
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from io import BytesIO


MONTHS = {name.lower(): i for i, name in enumerate(
    ('January', 'February', 'March', 'April', 'May', 'June', 'July',
     'August', 'September', 'October', 'November', 'December'), 1)}
DATE = re.compile(r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2}[- ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[- ]\d{4})\b', re.I)
TIME = re.compile(r'^\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?$', re.I)
DAY = re.compile(r'\b('+'|'.join(MONTHS)+r')\s+(\d{1,2})(?:st|nd|rd|th)?\b', re.I)


def parse_date(text):
    match=DATE.search(text)
    if not match: return None
    for fmt in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y','%d-%b-%Y','%d %b %Y','%d-%B-%Y','%d %B %Y'):
        try: return datetime.strptime(match.group(),fmt).date()
        except ValueError: pass
    return None


def amount(text):
    value=re.sub(r'(?:NGN|₦|\s|,)', '', text, flags=re.I)
    if value in ('','-','--','—','–'): return Decimal(0)
    sign=-1 if value.startswith('(') and value.endswith(')') else 1
    value=value.strip('()')
    suffix=re.search(r'(DR|CR)$',value,re.I)
    if suffix:
        sign=-1 if suffix.group().upper()=='DR' else 1
        value=value[:-2]
    if not re.fullmatch(r'[+-]?\d+\.\d{2}',value): raise ValueError('Ambiguous money cell')
    try:
        result=Decimal(value)*sign
        if not result.is_finite(): raise ValueError('Invalid amount')
        return result
    except InvalidOperation: raise ValueError('Invalid amount') from None


def lines(words):
    grouped=[]
    for word in sorted(words,key=lambda w:(w['top'],w['x0'])):
        if not grouped or abs(grouped[-1][0]['top']-word['top'])>3:
            grouped.append([word])
        else: grouped[-1].append(word)
    return [sorted(row,key=lambda w:w['x0']) for row in grouped]


def token(text):
    return re.sub(r'[^a-z]','',text.lower())


def header(row):
    """Find complete labelled inflow/outflow tables, including borderless PDFs."""
    cols=[];i=0
    while i<len(row):
        word=row[i];t=token(word['text']);n=token(row[i+1]['text']) if i+1<len(row) else ''
        role=None;span=1
        if t=='money' and n in ('in','out'):
            role='credit' if n=='in' else 'debit';span=2
        elif t.startswith(('withdrawal','debit')) or t=='dr': role='debit'
        elif t.startswith(('deposit','credit')) or t=='cr': role='credit'
        elif t=='balance': role='balance'
        elif t in ('description','narration','narrative','remarks','details','particulars','destination','category',
                   'recipient','beneficiary','counterparty','payee','beneficiaryname','recipientname'): role='description'
        elif t in ('trans','transaction','txn','posting') and n in ('date','time','details','detail','description','particulars','id','reference'):
            role='date' if n in ('date','time') else 'description' if n in ('details','detail','description','particulars') else 'ignore';span=2
        elif t in ('value','val') and n=='date': role='ignore';span=2
        elif t in ('date','time'): role='date'
        elif t in ('ref','reference','channel','chq','cheque'): role='ignore'
        if role:
            cols.append((word['x0']-2,role));i+=span
        else: i+=1
    roles=[role for _,role in cols]
    if 'debit' not in roles or 'credit' not in roles or 'description' not in roles: return None
    if roles.count('debit')!=1 or roles.count('credit')!=1 or roles.count('date')>1: return None
    if 'date' not in roles:
        # Kuda's grouped-day layout has a time column before Money In.
        if not DAY.search(' '.join(w['text'] for w in row)) and not {'category','destination'}.issubset({token(w['text']) for w in row}): return None
        cols.insert(0,(0,'date'))
    return cols


def header_rows(rows,index):
    """Understand headings wrapped over two visual lines without consuming data."""
    found=header(rows[index])
    if found: return found,1
    if index+1>=len(rows) or rows[index+1][0]['top']-rows[index][0]['top']>18: return None,1
    pair=rows[index]+rows[index+1]
    # Never merge a transaction/day heading into an incomplete header.
    if any(DATE.search(w['text']) or TIME.fullmatch(w['text']) or
           re.search(r'\d[,.]\d{2}',w['text']) for w in pair): return None,1
    # Group vertically aligned words, then read the resulting labels left to right.
    clusters=[]
    for word in sorted(pair,key=lambda w:w['x0']):
        if clusters and abs(clusters[-1][0]['x0']-word['x0'])<14:
            clusters[-1].append(word)
        else: clusters.append([word])
    merged=[]
    for cluster in clusters:
        for word in sorted(cluster,key=lambda w:(w['top'],w['x0'])):
            merged.append(word)
    return header(merged),2


def researched_guidance(row):
    """Apply researched exceptions only when source structure actually matches."""
    text=' '.join(token(w['text']) for w in row)
    if 'category' in text and 'destination' in text and 'money' in text:
        return ('Grouped-day format observed in Kuda: dates can be headings with time-only rows. '
                'Carry source day headings across pages; keep category, destination and narration attached to their row.')
    if 'channel' in text and 'reference' in text and 'value' in text:
        return ('Format observed in OPay: narration may wrap above AND below its transaction baseline. '
                'Use row alignment and spacing rather than blindly appending all text to the previous row. '
                'Wallet and Savings sections are distinct; do not join their balance chains.')
    if 'withdrawaldr' in text and 'depositcr' in text:
        return ('Withdrawal/Deposit format observed in First Bank: keep the reference and value date separate '
                'from the transaction date and amounts; join wrapped transaction details.')
    if 'value' in text and 'debit' in text and 'credit' in text:
        return ('Separate value-date format: use the transaction date for the report. '
                'Some Zenith totals include a brought-forward balance; only period-flow totals can verify payments.')
    return ''


def cells(row, cols):
    values={}
    for i,(left,role) in enumerate(cols):
        right=cols[i+1][0] if i+1<len(cols) else float('inf')
        text=' '.join(w['text'] for w in row if left<=w['x0']<right)
        if text: values[role]=(values.get(role,'')+' '+text).strip()
    return values


def document_context(reader):
    """Carry period and date headings into chunks without copying personal details."""
    texts=[page.extract_text() or '' for page in reader.pages]
    first=texts[0] if texts else ''
    # The first two explicit dates on a period line, never transaction dates.
    period=[]
    first_lines=first.splitlines()
    for index,line in enumerate(first_lines):
        spans=list(DATE.finditer(line));matches=[m.group() for m in spans]
        if len(matches)>=2 and (re.search(r'\b(?:period|from|date\s+range)\b',line,re.I) or
                                re.fullmatch(r'\s*(?:[-–—]|to)\s*',line[spans[0].end():spans[1].start()],re.I)):
            period=[parse_date(x) for x in matches[:2]];break
        if re.fullmatch(r'\s*(?:statement\s+)?(?:period|date)\s*:?\s*',line,re.I) and index+1<len(first_lines):
            matches=DATE.findall(first_lines[index+1])
            if len(matches)>=2: period=[parse_date(x) for x in matches[:2]];break
    period=[d for d in period if d]
    contexts=[];last_day=None
    for text in texts:
        contexts.append({'period':period,'day':last_day})
        matches=list(DAY.finditer(text))
        if matches: last_day=(MONTHS[matches[-1].group(1).lower()],int(matches[-1].group(2)))
    return contexts


def context_hint(context):
    bits=[]
    if len(context['period'])==2:
        bits.append('Source statement period: '+' to '.join(d.isoformat() for d in context['period'])+'.')
    if context['day']:
        month,day=context['day'];bits.append(f'Last printed day heading before these pages: month {month}, day {day}. It applies only until another source date heading.')
    return ' '.join(bits)


def table_hint(content):
    """Only structural coordinates, never names/narrations/account identifiers."""
    import pdfplumber
    with pdfplumber.open(BytesIO(content)) as pdf:
        for page in pdf.pages:
            rows=lines(page.extract_words())
            for index,row in enumerate(rows):
                cols,span=header_rows(rows,index)
                if cols:
                    ranges=[]
                    for i,(left,role) in enumerate(cols):
                        right=cols[i+1][0] if i+1<len(cols) else page.width
                        ranges.append(f'{role}: {max(0,left)/page.width:.3f} to {right/page.width:.3f}')
                    return ('First source transaction table column ranges as fractions of page width: '+
                            '; '.join(ranges)+'. Use this only for continuation pages with the same layout. '
                            'New printed column headings or a new account section take precedence. '+
                            researched_guidance([w for r in rows[index:index+span] for w in r]))
    return ''


def source_summary(content):
    """Read only the first-page summary above a recognised transaction header."""
    import pdfplumber
    with pdfplumber.open(BytesIO(content)) as pdf:
        rows=lines(pdf.pages[0].extract_words())
        for index,row in enumerate(rows):
            if header_rows(rows,index)[0]: return printed_summary(rows[:index])
    return {}


def resolve_day(match, period):
    if len(period)!=2: return None
    lo,hi=sorted(period)
    candidates=[]
    for year in range(lo.year,hi.year+1):
        try: candidate=date(year,MONTHS[match.group(1).lower()],int(match.group(2)))
        except ValueError: continue
        if lo<=candidate<=hi: candidates.append(candidate)
    return candidates[0] if len(candidates)==1 else None


def printed_summary(rows):
    labels={('opening','balance'):'opening_balance',('closing','balance'):'closing_balance',
            ('total','debit'):'total_debits',('total','debits'):'total_debits',
            ('total','credit'):'total_credits',('total','credits'):'total_credits',
            ('total','money','in'):'total_credits',('total','money','out'):'total_debits',
            ('money','in'):'total_credits',('money','out'):'total_debits'}
    labels.update({('debit','count'):'debit_count',('credit','count'):'credit_count'})
    found={}
    for index,row in enumerate(rows):
        matches=[]
        for i in range(len(row)):
            for phrase,key in sorted(labels.items(),key=lambda x:-len(x[0])):
                if tuple(token(w['text']) for w in row[i:i+len(phrase)])==phrase:
                    if i and token(row[i-1]['text'])=='total': continue
                    matches.append((i,len(phrase),key));break
        for n,(i,length,key) in enumerate(matches):
            left=row[i]['x0']-2
            right=row[matches[n+1][0]]['x0']-2 if n+1<len(matches) else float('inf')
            inline=' '.join(w['text'] for w in row[i+length:] if w['x0']<right)
            below=[' '.join(w['text'] for w in r if left<=w['x0']<right)
                   for r in rows[index+1:index+4] if r[0]['top']-row[0]['top']<32]
            for candidate in [inline]+below:
                if key.endswith('_count'):
                    if candidate.strip().isdigit(): found[key]=int(candidate.strip());break
                    continue
                # Accept only one printed money value, never pick from surrounding data.
                if not re.fullmatch(r'\s*(?:NGN\s*|₦\s*)?[\d,]+\.\d{2}\s*',candidate,re.I): continue
                value=str(amount(candidate))
                if key in found and found[key]!=value: return {} # multiple account summaries
                found[key]=value;break
    return found


def read_wallet_columns(content, reader):
    """Read the observed OPay wallet table with nearest-row narration attachment.

    Separate savings sections are rejected, never silently dropped. Printed
    debit/credit counts are required so an omitted row cannot pass unnoticed.
    """
    import pdfplumber
    result={'complete':True,'currency':'NGN','page_count':len(reader.pages),'transactions':[]}
    debit_count=credit_count=0;previous_cols=None;previous_width=None
    with pdfplumber.open(BytesIO(content)) as pdf:
        for page_no,page in enumerate(pdf.pages):
            words=page.extract_words();rows=lines(words)
            if not words: return None
            text=' '.join(w['text'] for w in words)
            if re.search(r'Savings\s+Account',text,re.I): return None
            selected=None
            for i,row in enumerate(rows):
                cols,span=header_rows(rows,i)
                if not cols or not any(role=='balance' for _,role in cols): continue
                tokens={token(w['text']) for r in rows[i:i+span] for w in r}
                if {'channel','reference','value'}.issubset(tokens):
                    selected=(i,span,cols);break
            if not selected:
                if previous_cols is None or previous_width!=page.width: return None
                selected=(-1,1,previous_cols)
            i,span,cols=selected
            previous_cols=cols;previous_width=page.width
            if page_no==0:
                result.update(printed_summary(rows[:i]))
                if not all(k in result for k in ('opening_balance','closing_balance','total_debits','total_credits','debit_count','credit_count')): return None
            anchors=[]
            for row in rows[i+span:]:
                values=cells(row,cols);day=parse_date(values.get('date',''))
                if not day: continue
                debit=amount(values.get('debit',''));credit=amount(values.get('credit',''))
                if (debit>0)==(credit>0) or debit<0 or credit<0 or not values.get('balance'): return None
                balance=amount(values['balance'])
                date_words=[w for w in row if cols[0][0]<=w['x0']<cols[1][0]]
                y=min(w['top'] for w in date_words)
                anchors.append((y,{'date':day.isoformat(),'amount':str(debit or credit),
                    'direction':'debit' if debit else 'credit','balance':str(balance),'confidence':1.,'description':''}))
                debit_count+=int(debit>0);credit_count+=int(credit>0)
            if not anchors: return None
            desc_left=next(left for left,role in cols if role=='description')
            desc_right=next(left for left,role in cols if role in ('debit','credit'))
            header_bottom=max(w['top'] for r in rows[i:i+span] for w in r)+5 if i>=0 else 0
            buckets=[[] for _ in anchors]
            # Alternating shaded cells encode actual transaction boundaries.
            # Prefer those source boundaries to a nearest-baseline guess for
            # tall rows containing recipient names and long payment notes.
            regions=[]
            for rect in page.rects:
                if rect['x0']<=desc_left<rect['x1'] and rect['x1']<=desc_right+3 and rect['bottom']-rect['top']>10:
                    members=[n for n,(y,_) in enumerate(anchors) if rect['top']<=y<rect['bottom']]
                    if len(members)==1: regions.append((rect['top'],rect['bottom'],members[0]))
            for word in words:
                if not desc_left<=word['x0']<desc_right or word['top']<=header_bottom: continue
                bounded=[n for top,bottom,n in regions if top<=word['top']<bottom]
                nearest=bounded[0] if len(set(bounded))==1 else min(range(len(anchors)),key=lambda n:abs(word['top']-anchors[n][0]))
                if abs(word['top']-anchors[nearest][0])>48: return None
                buckets[nearest].append(word)
            for (_,transaction),bucket in zip(anchors,buckets):
                transaction['description']=' '.join(w['text'] for row in lines(bucket) for w in row)
                if not transaction['description']: return None
                result['transactions'].append(transaction)
    if debit_count!=result['debit_count'] or credit_count!=result['credit_count']: return None
    result['transaction_count']=debit_count+credit_count
    result['source_reader']='wallet_columns'
    return result


def read_labelled_pdf(content, reader):
    """Return a full extraction only when every source transaction is understood.

    This reader never infers direction from merchant words or a balance delta.
    The caller must reconcile it before using any result.
    """
    import pdfplumber
    contexts=document_context(reader);period=contexts[0]['period']
    first_text=reader.pages[0].extract_text() or ''
    if not re.search(r'₦|\bNGN\b|\bnaira\b',first_text,re.I): return None
    if re.search(r'\b(?:USD|GBP|EUR|dollars?|pounds?|euros?)\b',first_text,re.I): return None
    result={'complete':True,'currency':'NGN','page_count':len(reader.pages),'transactions':[]}
    cols=None;current_day=None;pending=None;seen_header=False
    with pdfplumber.open(BytesIO(content)) as pdf:
        width=None
        for page in pdf.pages:
            if width is not None and abs(width-page.width)>1: return None
            width=page.width
            words=page.extract_words()
            if not words: return None # scanned/mixed pages require the AI reader
            page_rows=lines(words)
            if not seen_header:
                # Summaries above the first transaction header only.
                first_header=next((i for i,r in enumerate(page_rows) if header_rows(page_rows,i)[0]),len(page_rows))
                result.update(printed_summary(page_rows[:first_header]))
            skip_until=0
            for index,row in enumerate(page_rows):
                if index<skip_until: continue
                text=' '.join(w['text'] for w in row)
                found,span=header_rows(page_rows,index)
                if found:
                    heading_words=[w for r in page_rows[index:index+span] for w in r]
                    # Pre-row narration attachment requires the visual fallback.
                    if {'channel','reference','value'}.issubset({token(w['text']) for w in heading_words}):
                        return read_wallet_columns(content,reader)
                    cols=found;seen_header=True
                    skip_until=index+span
                    match=DAY.search(text)
                    if match: current_day=resolve_day(match,period)
                    continue
                if not seen_header:
                    match=DAY.search(text)
                    if match: current_day=resolve_day(match,period)
                    continue
                # Exclude printed page chrome before touching the pending narration.
                if re.match(r'^(?:Kuda MF Bank|Account Number\s*:|Page \d+|Statement$|All rights|is licensed)',text,re.I): continue
                values=cells(row,cols)
                match=DAY.search(values.get('date',''))
                if match:
                    current_day=resolve_day(match,period);continue
                date_cell=values.get('date','')
                day=parse_date(date_cell)
                if not day and TIME.fullmatch(date_cell): day=current_day
                # A complete new money row with an empty date cell inherits the
                # preceding printed date, as in grouped/ditto-date bank tables.
                inherited=(not date_cell and current_day and values.get('description') and values.get('balance') and
                           any(re.search(r'\d[,.]\d{2}',values.get(k,'')) for k in ('debit','credit')))
                if inherited: day=current_day
                is_candidate=bool(DATE.search(date_cell) or TIME.fullmatch(date_cell) or inherited)
                if is_candidate:
                    if not day: return None
                    current_day=day
                    try:
                        debit=amount(values.get('debit',''));credit=amount(values.get('credit',''))
                        balance=amount(values['balance']) if values.get('balance') else None
                    except ValueError: return None
                    if debit<0 or credit<0 or (debit>0)==(credit>0): return None
                    if pending: result['transactions'].append(pending)
                    pending={'date':day.isoformat(),'description':values.get('description',''),
                             'amount':str(debit or credit),'direction':'debit' if debit else 'credit',
                             'balance':str(balance) if balance is not None else None,'confidence':1.0}
                elif pending:
                    # Amounts on a continuation row may be a split transaction:
                    # let the fallback reader handle it rather than silently lose it.
                    for key in ('debit','credit','balance'):
                        cell=values.get(key,'')
                        if re.search(r'\d[,.]\d{2}',cell): return None
                    if values.get('description'):
                        pending['description']+=' '+values['description']
        if pending: result['transactions'].append(pending)
    if not result['transactions'] or any(not r['description'].strip() or r['balance'] is None for r in result['transactions']): return None
    # Avoid treating a lone row or an unanchored partial table as a verified read.
    if len(result['transactions'])<2: return None
    if any(key not in result for key in ('opening_balance','closing_balance')): return None
    return result
