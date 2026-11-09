(() => {
  const script = document.currentScript;
  const root = new URL('../',script.src);
  const box = document.getElementById('analises-publicadas');
  if (!box) return;
  let entries = [];
  function update() {
    const uf = document.getElementById('uf')?.value || '';
    const municipio = document.getElementById('municipio')?.value || '';
    const cargo = document.getElementById('cargo')?.value || '';
    const selected = entries.filter(item=>item.uf === uf && item.municipio === municipio && (!cargo || item.cargos.includes(cargo)));
    const anchor = box.querySelector('a');
    const url = new URL('analises/',root); if (uf) url.searchParams.set('uf',uf); if (/^\d{5}$/.test(municipio)) url.searchParams.set('municipio',municipio); if (cargo) url.searchParams.set('cargo',cargo);
    anchor.href = url.href;
    box.querySelector('[data-analysis-note]').textContent = selected.length ? selected[0].nome + ' · ' + selected.length + ' versão(ões) publicada(s).' : document.documentElement.lang.startsWith('en') ? 'Read the municipal analyses in Portuguese.' : 'Consulte as análises disponíveis e suas versões.';
  }
  document.addEventListener('atlas:territorychange',update);
  for (const id of ['uf','municipio','cargo']) document.getElementById(id)?.addEventListener('change',update);
  fetch(new URL('analises/catalogo.json',root),{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('catalog');return r.json();}).then(c=>{if(c.schema!==1||!Array.isArray(c.analises))throw Error('schema');entries=c.analises;update();}).catch(update);
  update();
})();
