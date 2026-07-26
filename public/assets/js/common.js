const ARES={
 async json(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(`${url}: HTTP ${r.status}`);return r.json()},
 query(name){return new URLSearchParams(location.search).get(name)},
 esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))},
 async schools(){return this.json('schools/index.json')},
 async school(code){return this.json(`schools/${encodeURIComponent(code)}.json`)},
 storageKey(code){return `ares-setup-${code}`}
};
