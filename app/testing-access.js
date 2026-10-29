// Included only in the Vercel build. No Gemini key is ever sent to the browser.
(()=>{const originalFetch=window.fetch.bind(window);window.fetch=async(input,options={})=>{
 if(input!=='/api/parse')return originalFetch(input,options);
 let code=sessionStorage.getItem('nawa-test-code');
 if(!code){code=window.prompt('Enter the NAWA tester access code shared with you.');if(code)sessionStorage.setItem('nawa-test-code',code)}
 const response=await originalFetch(input,{...options,headers:{...options.headers,'X-Nawa-Test-Code':code||''}});
 if(response.status===401)sessionStorage.removeItem('nawa-test-code');
 return response;
}})();
