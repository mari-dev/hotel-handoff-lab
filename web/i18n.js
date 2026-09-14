// UI translations only: never translate guest input or source quotations.
const supportedLanguages=['en','de','it'];
let language='en';
try { const saved=localStorage.getItem('invoice-language'); if(supportedLanguages.includes(saved))language=saved; } catch {}
i18next.init({lng:language,fallbackLng:'en',supportedLngs:supportedLanguages,resources:window.invoiceLocales,keySeparator:false,nsSeparator:false,initImmediate:false,interpolation:{escapeValue:false}});
const t=key=>{
  // Re-localize an already visible system message after a language switch.
  if(!Object.hasOwn(invoiceLocales.en.translation,key)){
    for(const code of supportedLanguages){
      const found=Object.entries(invoiceLocales[code].translation).find(([,value])=>value===key);
      if(found){key=found[0];break;}
    }
  }
  return i18next.t(key);
};
function systemText(value){
  for(const prefix of ['PDF detected: ','Exported email with identical PDF: '])
    if(value.startsWith(prefix))return t(prefix)+value.slice(prefix.length);
  return t(value);
}
function localize(root=document){
  root.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});
  for(const attr of ['placeholder','aria-label'])root.querySelectorAll('[data-i18n-'+attr+']').forEach(el=>el.setAttribute(attr,t(el.getAttribute('data-i18n-'+attr))));
  document.documentElement.lang=language;document.title=t('Invoices · Reception');
}
