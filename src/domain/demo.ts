import { Transaction } from './types';
export const demoTransactions:Transaction[]=[
 {id:'d1',date:'2026-08-01',description:'Monthly salary · Acme Studio',amount:485000,type:'income',category:'Income',needsReview:false},
 {id:'d2',date:'2026-08-02',description:'Shoprite Lekki',amount:38250,type:'expense',category:'Food & groceries',needsReview:false},
 {id:'d3',date:'2026-08-03',description:'Bolt ride',amount:6800,type:'expense',category:'Transport',needsReview:false},
 {id:'d4',date:'2026-08-05',description:'Transfer to savings',amount:50000,type:'review',category:'Needs review',needsReview:true},
 {id:'d5',date:'2026-08-07',description:'Airtel data bundle',amount:7500,type:'expense',category:'Bills & subscriptions',needsReview:false},
 {id:'d6',date:'2026-08-09',description:'Dinner at Yellow Chilli',amount:18500,type:'expense',category:'Food & groceries',needsReview:false},
 {id:'d7',date:'2026-08-12',description:'Eko Electricity',amount:22000,type:'expense',category:'Home',needsReview:false},
 {id:'d8',date:'2026-08-14',description:'Pharmacy Plus',amount:12400,type:'expense',category:'Health',needsReview:false},
 {id:'d9',date:'2026-08-16',description:'Jumia order refund',amount:8900,type:'refund',category:'Refunds',needsReview:false},
 {id:'d10',date:'2026-08-18',description:'Netflix monthly',amount:4900,type:'expense',category:'Bills & subscriptions',needsReview:false},
 {id:'d11',date:'2026-08-20',description:'Fuel · Mobil Ikoyi',amount:28000,type:'expense',category:'Transport',needsReview:false},
 {id:'d12',date:'2026-08-23',description:'Sunday market',amount:16200,type:'expense',category:'Food & groceries',needsReview:false},
 {id:'d13',date:'2026-08-26',description:'Transfer received · Chika',amount:20000,type:'review',category:'Needs review',needsReview:true},
 {id:'d14',date:'2026-08-28',description:'Spotify',amount:1800,type:'expense',category:'Bills & subscriptions',needsReview:false},
 {id:'d15',date:'2026-08-30',description:'Uber ride',amount:5400,type:'expense',category:'Transport',needsReview:false}
];
export const previousDemo:Transaction[]=demoTransactions.map((t,i)=>({...t,id:`p${i}`,date:t.date.replace('2026-08','2026-07'),amount:Math.round(t.amount*(0.78+(i%4)*.09)),description:t.description.replace('Monthly salary','Monthly salary')}));
