import {describe,it,expect} from 'vitest';
import {parseCsv} from '../src/services/csv';
describe('CSV statement parser',()=>{
 it('handles quoted commas, debit and credit columns, and review categories',()=>{const p=parseCsv('Date,Description,Debit,Credit\n01/08/2026,"Cafe, Victoria Island",2500,\n02/08/2026,Salary,,125000\n03/08/2026,Transfer to savings,20000,');expect(p.transactions).toHaveLength(3);expect(p.transactions[0].description).toBe('Cafe, Victoria Island');expect(p.transactions[0].date).toBe('2026-08-01');expect(p.transactions[0].type).toBe('expense');expect(p.transactions[1].type).toBe('income');expect(p.transactions[2].needsReview).toBe(true);});
 it('skips duplicate and malformed rows with a note',()=>{const p=parseCsv('date,description,amount\n2026-08-01,Shoprite,2500\n2026-08-01,Shoprite,2500\n,Missing date,500');expect(p.transactions).toHaveLength(1);expect(p.warnings).toHaveLength(2);});
 it('rejects empty files and files with no valid transactions',()=>{expect(()=>parseCsv('  ')).toThrow('empty');expect(()=>parseCsv('date,description,amount\n')).toThrow();});
 it('handles signed amounts and refunds',()=>{const p=parseCsv('date,description,amount\n2026-08-01,Salary,100000\n2026-08-02,Shoprite,-2500\n2026-08-03,Order refund,4000');expect(p.transactions[0].type).toBe('income');expect(p.transactions[1].type).toBe('expense');expect(p.transactions[2].type).toBe('refund');});
});
