import {describe,it,expect} from 'vitest';
import {byCategory,classify,reportFrom,sumByType} from '../src/domain/finance';
import {Transaction} from '../src/domain/types';
import {demoTransactions} from '../src/domain/demo';
const tx=(id:string,type:Transaction['type'],amount:number,date='2026-08-01',category='Other'):Transaction=>({id,type,amount,date,category,description:id,needsReview:type==='review'});
describe('Nawa money definitions',()=>{
 it('keeps income, gross spending, transfers and refunds separate',()=>{const v=[tx('salary','income',100000),tx('shop','expense',20000),tx('move','transfer',15000),tx('back','refund',5000)];expect(sumByType(v)).toEqual({income:100000,spending:20000,transfers:15000,refunds:5000,remaining:85000,grossOutflow:35000});});
 it('excludes uncertain transactions from calculated totals',()=>{const v=sumByType([tx('review','review',9000),tx('x','expense',1000)]);expect(v.spending).toBe(1000);expect(v.remaining).toBe(-1000);});
 it('groups spending categories only',()=>{expect(byCategory([tx('one','expense',25,'2026-08-01','Food'),tx('two','expense',10,'2026-08-02','Food'),tx('in','income',100,'2026-08-03','Income')])).toEqual([{category:'Food',amount:35}]);});
 it('calculates the sample report from its underlying transactions',()=>{const r=reportFrom(demoTransactions,'sample',true);expect(sumByType(r.transactions).income).toBe(485000);expect(sumByType(r.transactions).spending).toBe(161750);expect(sumByType(r.transactions).transfers).toBe(0);expect(sumByType(r.transactions).refunds).toBe(8900);});
 it('flags transfers and unknown merchants for review, without guessing',()=>{expect(classify('Transfer to savings',-3000).type).toBe('review');expect(classify('Mystery merchant',3000).needsReview).toBe(true);expect(classify('Mystery merchant',-3000).type).toBe('expense');expect(classify('Salary payment',90000).type).toBe('income');});
});
