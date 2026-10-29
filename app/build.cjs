// Publish only browser assets; never publish the Python server or private runtime files.
const fs=require('fs'),path=require('path');const dist=path.join(__dirname,'dist');fs.mkdirSync(dist,{recursive:true});
for(const name of ['index.html','phone.html','manifest.json','app.js','style.css','design-update.css','delight.css','premium-onboarding.css','themes.css','testing-access.js']){
 let data=fs.readFileSync(path.join(__dirname,name),'utf8');
 if(name==='app.js')data=data.replaceAll('12 MB','4 MB').replaceAll('file.size>12*1024*1024','file.size>4*1024*1024');
 if(name==='index.html')data=data.replace('<script src="app.js">','<script src="testing-access.js"></script><script src="app.js">');
 fs.writeFileSync(path.join(dist,name),data);
}
fs.cpSync(path.join(__dirname,'assets'),path.join(dist,'assets'),{recursive:true});
console.log('Built browser assets in dist. Backend remains private in api/parse.py.');
