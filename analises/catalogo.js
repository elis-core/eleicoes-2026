const byId = id => document.getElementById(id);
const parameters = new URLSearchParams(location.search);
const normalize = value => String(value).normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
const version = value => value.split('.').map(Number);
const compareVersion = (a, b) => { const x = version(a), y = version(b); return (x[0] - y[0]) || (x[1] - y[1]) || ((x[2] || 0) - (y[2] || 0)); };
const link = (text, url) => { const a = document.createElement('a'); a.textContent = text; a.href = url; return a; };
let catalog;
function render() {
  const uf = byId('analise-uf').value;
  const text = normalize(byId('analise-nome').value.trim());
  const cargo = byId('analise-cargo').value;
  const list = byId('analise-lista'); list.replaceChildren();
  const selected = catalog.analises.filter(item => (!uf || item.uf === uf) && (!cargo || item.cargos.includes(cargo)) && (!text || normalize(item.nome + ' ' + item.municipio).includes(text)) && (!parameters.get('municipio') || item.municipio === parameters.get('municipio')));
  const groups = new Map();
  for (const item of selected) { const id = item.uf + ':' + item.municipio + ':' + item.ano; if (!groups.has(id)) groups.set(id, []); groups.get(id).push(item); }
  const municipalities = [...groups.values()].sort((a,b) => a[0].nome.localeCompare(b[0].nome, 'pt-BR'));
  for (const versions of municipalities) {
    versions.sort((a,b) => compareVersion(b.versao,a.versao));
    const current = versions[0]; const article = document.createElement('article'); article.className = 'panel';
    const heading = document.createElement('h2'); heading.textContent = current.nome + ' · ' + current.uf;
    const info = document.createElement('p'); info.textContent = current.ano + ' · versão ' + current.versao + ' · ' + current.data.split('-').reverse().join('/') + ' · publicado por elis-atlas-publisher';
    const actions = document.createElement('div'); actions.className = 'analysis-actions';
    actions.append(link('Ler análise', current.arquivos.html.url));
    if (current.arquivos.pdf) actions.append(link('Baixar PDF', current.arquivos.pdf.url));
    const selectedOffice = cargo || 'presidente'; const turns = current.periodos?.[selectedOffice] || [1]; const turn = String(Math.max(...turns));
    const explorer = new URL('../', location.href); explorer.search = new URLSearchParams({cargo:selectedOffice,uf:current.uf,municipio:current.municipio,mode:'analisar',turno:turn}); explorer.hash = 'explorador';
    actions.append(link('Explorar resultados', explorer.href)); article.append(heading,info,actions);
    if (versions.length > 1) { const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = 'Versões anteriores'; details.append(summary); for (const old of versions.slice(1)) { const p = document.createElement('p'); p.append(link('Versão ' + old.versao + ' · ' + old.data,old.arquivos.html.url)); details.append(p); } article.append(details); }
    list.append(article);
  }
  byId('analise-status').textContent = !catalog.analises.length ? 'As análises municipais aparecerão aqui após sua publicação.' : municipalities.length + (municipalities.length === 1 ? ' município encontrado.' : ' municípios encontrados.');
}
try {
  const response = await fetch('catalogo.json', {cache:'no-cache'}); if (!response.ok) throw new Error('catalog');
  catalog = await response.json(); if (catalog.schema !== 1 || !Array.isArray(catalog.analises)) throw new Error('schema');
  for (const state of [...new Set(catalog.analises.map(item=>item.uf))].sort()) byId('analise-uf').add(new Option(state,state));
  byId('analise-uf').value = parameters.get('uf') || '';
  byId('analise-cargo').value = parameters.get('cargo') || '';
  byId('analise-filtros').addEventListener('submit', event=>{event.preventDefault(); parameters.delete('municipio'); render();});
  for (const id of ['analise-uf','analise-nome','analise-cargo']) byId(id).addEventListener('input',()=>{parameters.delete('municipio');render();});
  render();
} catch { byId('analise-status').textContent = 'Não foi possível carregar o catálogo. Recarregue a página.'; }
