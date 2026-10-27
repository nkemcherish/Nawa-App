import {Report} from '../domain/types';
export const REPORTS_KEY='nawa.reports.v1';
export type LocalStorage={getItem:(key:string)=>Promise<string|null>;setItem:(key:string,value:string)=>Promise<void>};
export async function readReports(storage:LocalStorage):Promise<Report[]>{
 const raw=await storage.getItem(REPORTS_KEY);if(!raw)return [];
 try{const value=JSON.parse(raw);if(!Array.isArray(value))return [];return value.filter((r):r is Report=>Boolean(r&&typeof r==='object'&&typeof r.id==='string'&&typeof r.title==='string'&&Array.isArray(r.transactions)&&typeof r.createdAt==='string'));}catch{return [];}
}
export async function writeReports(storage:LocalStorage,reports:Report[]):Promise<void>{await storage.setItem(REPORTS_KEY,JSON.stringify(reports));}
