import Papa from 'papaparse';
import { classify } from '../domain/finance';
import { Transaction } from '../domain/types';
const normal=(s:string)=>s.trim().toLowerCase().replace(/[ _-]/g,'');
const pick=(row:Record<string,unknown>,...keys:string[])=>{for(const k of keys){const found=Object.keys(row).find(h=>normal(h)===normal(k));if(found)return String(row[found]??'').trim();}return '';};
export function parseCsv(text:string):{transactions:Transaction[];warnings:string[]} {
 if(!text.trim()) throw new Error('This file is empty. Choose a CSV with transaction rows.');
 const result=Papa.parse<Record<string,unknown>>(text,{header:true,skipEmptyLines:'greedy',dynamicTyping:false});
 if(result.errors.length && result.data.length===0) throw new Error('We could not read this CSV. Check that it has a header row and try again.');
 const transactions:Transaction[]=[]; const warnings:string[]=[]; const seen=new Set<string>();
 result.data.forEach((row,index)=>{
  const dateRaw=pick(row,'date','transaction date','posted date'), description=pick(row,'description','details','narration','merchant','transaction');
  const amountRaw=pick(row,'amount','value'); const debit=pick(row,'debit'),credit=pick(row,'credit');
  const parsedDate=parseDate(dateRaw); let amount=amountRaw.trim()?Number(amountRaw.replace(/[₦,\s]/g,'')):NaN;
  let typeAmount=amount;
  if(!Number.isFinite(amount)){const d=Number(debit.replace(/[₦,\s]/g,''))||0,c=Number(credit.replace(/[₦,\s]/g,''))||0;if(d||c){amount=d||c;typeAmount=c?Math.abs(c):-Math.abs(d);} }
  if(!parsedDate||!description||!Number.isFinite(amount)||amount===0){warnings.push(`Row ${index+2} was skipped because its date, description, or amount is missing or invalid.`);return;}
  const sign=amountRaw.trim().startsWith('-')?-1:1; const magnitude=Math.abs(amount);
  const classified=classify(description,typeAmount || sign*magnitude);
  const hasDirectionColumns=Boolean(debit||credit),signedAmount=/^[+-]/.test(amountRaw.trim());
  if(amountRaw.trim()&&!hasDirectionColumns&&!signedAmount&&classified.type==='income'&&!/salary|payroll|interest|dividend|income|allowance/i.test(description)){
   classified.type='review';classified.category='Needs review';classified.needsReview=true;
  }
  const fingerprint=[parsedDate,description.toLowerCase(),magnitude].join('|');
  if(seen.has(fingerprint)){warnings.push(`A duplicate transaction on row ${index+2} was skipped.`);return;} seen.add(fingerprint);
  transactions.push({id:`csv_${index}_${fingerprint.length}`,date:parsedDate,description,amount:magnitude,type:classified.type,category:classified.category,needsReview:classified.needsReview});
 });
 if(!transactions.length) throw new Error(warnings[0]||'No valid transactions were found.');
 return {transactions,warnings};
}
function parseDate(s:string):string|null {const v=s.trim(); if(!v)return null; let m=v.match(/^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$/);if(m)return `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;m=v.match(/^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$/);if(m){const day=Number(m[1]),month=Number(m[2]),y=m[3];if(month>12||day>31)return null;return `${y}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;}const d=new Date(v);return Number.isNaN(d.getTime())?null:d.toISOString().slice(0,10);}
