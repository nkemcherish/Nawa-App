import {describe,it,expect} from 'vitest';
import {readReports,REPORTS_KEY,writeReports,LocalStorage} from '../src/services/reportStore';
import {reportFrom} from '../src/domain/finance';
import {demoTransactions} from '../src/domain/demo';
function memoryStore():LocalStorage&{data:Map<string,string>}{const data=new Map<string,string>();return {data,getItem:async key=>data.get(key)??null,setItem:async(key,value)=>{data.set(key,value);}};}
describe('local saved reports',()=>{
 it('saves reports and reopens them from persistent storage',async()=>{const store=memoryStore();const report=reportFrom(demoTransactions,'sample',true);await writeReports(store,[report]);const reopened=await readReports(store);expect(reopened).toHaveLength(1);expect(reopened[0].id).toBe(report.id);expect(reopened[0].transactions).toHaveLength(demoTransactions.length);});
 it('recovers cleanly from missing or corrupt saved data',async()=>{const store=memoryStore();expect(await readReports(store)).toEqual([]);store.data.set(REPORTS_KEY,'{broken');expect(await readReports(store)).toEqual([]);});
 it('persists deletion as an empty report list',async()=>{const store=memoryStore();await writeReports(store,[reportFrom(demoTransactions,'sample',true)]);await writeReports(store,[]);expect(await readReports(store)).toEqual([]);});
});
