import { Report, Totals, Transaction, TxType } from './types';

export const money = (amount: number) => new Intl.NumberFormat('en-NG', { style:'currency', currency:'NGN', maximumFractionDigits:0 }).format(amount);
export const prettyDate = (iso:string) => new Date(`${iso}T12:00:00`).toLocaleDateString('en-NG',{day:'numeric',month:'short'});
export const sumByType = (transactions: Transaction[]): Totals => {
  const total = (type:TxType) => transactions.filter(t=>t.type===type&&!t.needsReview).reduce((s,t)=>s+t.amount,0);
  const income=total('income'), spending=total('expense'), transfers=total('transfer'), refunds=total('refund');
  return {income,spending,transfers,refunds,remaining:income-spending+refunds,grossOutflow:spending+transfers};
};
export const byCategory = (transactions:Transaction[]) => {
  const map = new Map<string,number>();
  transactions.filter(t=>t.type==='expense'&&!t.needsReview).forEach(t=>map.set(t.category,(map.get(t.category)||0)+t.amount));
  return [...map.entries()].map(([category,amount])=>({category,amount})).sort((a,b)=>b.amount-a.amount);
};
export const periodOf = (transactions:Transaction[]) => {
  const dates=transactions.map(t=>t.date).sort();
  return {periodStart:dates[0]||new Date().toISOString().slice(0,10),periodEnd:dates.at(-1)||new Date().toISOString().slice(0,10)};
};
export const reportFrom = (transactions:Transaction[],source:string,isDemo=false):Report => {
  const p=periodOf(transactions); const date=new Date(`${p.periodEnd}T12:00:00`);
  return {id:`r_${Date.now()}_${Math.random().toString(36).slice(2,7)}`,title:date.toLocaleDateString('en-NG',{month:'long',year:'numeric'}),createdAt:new Date().toISOString(),source,isDemo,transactions:transactions.map(t=>({...t})),...p};
};
export const classify = (description:string, amount:number):{type:TxType;category:string;needsReview:boolean} => {
  const d=description.toLowerCase();
  if(/refund|reversal|cashback/.test(d)) return {type:'refund',category:'Refunds',needsReview:false};
  if(/transfer|xfer|own account|wallet top.?up/.test(d)) return {type:'review',category:'Needs review',needsReview:true};
  if(/salary|payroll|interest|dividend|income|allowance/.test(d)) return {type:'income',category:'Income',needsReview:false};
  if(/uber|bolt|ride|transport|fuel/.test(d)) return {type:'expense',category:'Transport',needsReview:false};
  if(/shoprite|market|grocery|food|restaurant|cafe/.test(d)) return {type:'expense',category:'Food & groceries',needsReview:false};
  if(/netflix|spotify|airtel|mtn|data|subscription/.test(d)) return {type:'expense',category:'Bills & subscriptions',needsReview:false};
  if(/pharmacy|hospital|clinic/.test(d)) return {type:'expense',category:'Health',needsReview:false};
  if(/rent|electric|ikeja|eko electric/.test(d)) return {type:'expense',category:'Home',needsReview:false};
  if(amount<0) return {type:'expense',category:'Other',needsReview:false};
  return {type:'review',category:'Needs review',needsReview:true};
};
export const makeObservations=(transactions:Transaction[]) => {
 const cats=byCategory(transactions), largest=cats[0];
 const days=new Map<string,number>(); transactions.filter(t=>t.type==='expense').forEach(t=>days.set(t.date,(days.get(t.date)||0)+t.amount));
 const maxDay=[...days.entries()].sort((a,b)=>b[1]-a[1])[0];
 const out:string[]=[];
 if(largest) out.push(`${largest.category} was your biggest spending category at ${money(largest.amount)}.`);
 if(maxDay) out.push(`Your highest-spend day was ${prettyDate(maxDay[0])} (${money(maxDay[1])}).`);
 const reviews=transactions.filter(t=>t.needsReview).length;
 if(reviews) out.push(`${reviews} ${reviews===1?'transaction needs':'transactions need'} your review before this report is complete.`);
 return out;
};
