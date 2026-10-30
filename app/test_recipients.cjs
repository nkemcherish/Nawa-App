const fs=require('fs'),vm=require('vm'),assert=require('assert');
const context={localStorage:{getItem:()=>null,setItem:()=>{}},document:{querySelector:()=>({innerHTML:''})},window:{scrollTo:()=>{}},console,assert};
vm.createContext(context);
vm.runInContext(fs.readFileSync(__dirname+'/app.js','utf8')+`
state.isDemo=false;const key='abcdef0123456789abcd';
state.transactions=Array.from({length:6},(_,i)=>({id:'test-'+i,date:'2026-10-01',description:'Transfer to Fictional Person / ref '+i,amount:100,direction:'debit',type:'expense',category:'Fictional Person',categoryKind:'recipient',review:false,recipientName:'Fictional Person',recipientGroup:'Fictional Person',recipientKey:key}));
assert.equal(repeatedRecipients().length,1);assert.equal(stats(state.transactions).spend,600);
assert(report().includes('Repeated recipients'));
openCategory(availableCategories().indexOf('Fictional Person'));assert.equal(state.category,'Fictional Person');assert(categoryDetail().includes('purpose has not been confirmed'));
openRecipient(0);assert.equal(state.view,'recipientDetail');assert(recipientDetail().includes('ref 5'));
toggleOwnRecipient(0);assert.equal(stats(state.transactions).spend,0);assert(state.transactions.every(t=>t.category==='Savings'));assert(report().includes('Savings & own accounts'));
openCategory(cats.indexOf('Savings'));assert(categoryDetail().includes('MOVED TO SAVINGS'));
const backup=validateBackup({format:'nawa-backup',version:1,reports:[{transactions:state.transactions}]});assert.equal(backup[0].transactions[0].recipientKey,key);assert.equal(backup[0].transactions[0].recipientOriginal.category,'Fictional Person');
toggleOwnRecipient(0);assert.equal(stats(state.transactions).spend,600);
toggleOwnRecipient(0);const future=applyOwnRecipientRules([{recipientKey:key,type:'expense',category:'Food & drinks',review:false}]);assert.equal(future[0].category,'Savings');
state.transactions=backup[0].transactions;assert.equal(repeatedRecipients().length,1);
state.transactions=Array.from({length:5},(_,i)=>({direction:'debit',recipientKey:key,recipientName:'Fictional Person',amount:100,type:'expense'}));assert.equal(repeatedRecipients().length,0);
console.log('Savings, dynamic categories, recipient views, own-account memory and backups passed');
`,context);
