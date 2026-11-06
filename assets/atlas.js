"use strict";

const locale = document.documentElement.lang;
const english = locale.startsWith("en");
const t = (pt, en) => english ? en : pt;
const dataRoot = new URL("../dados/", document.currentScript.src);
const $ = (id) => document.getElementById(id);
const form = $("filters");
const languageSwitch = $("language-switch");
const alternatePage = languageSwitch.href;
const uf = $("uf");
const municipio = $("municipio");
const local = $("local");
const secao = $("secao");
const geoHint = $("geo-hint");
const year = 2026;
const municipalList = "lista";
const states = {AC:"Acre", AL:"Alagoas", AP:"Amapá", AM:"Amazonas", BA:"Bahia", CE:"Ceará",
  DF:"Distrito Federal", ES:"Espírito Santo", GO:"Goiás", MA:"Maranhão", MT:"Mato Grosso",
  MS:"Mato Grosso do Sul", MG:"Minas Gerais", PA:"Pará", PB:"Paraíba", PR:"Paraná",
  PE:"Pernambuco", PI:"Piauí", RJ:"Rio de Janeiro", RN:"Rio Grande do Norte",
  RS:"Rio Grande do Sul", RO:"Rondônia", RR:"Roraima", SC:"Santa Catarina",
  SP:"São Paulo", SE:"Sergipe", TO:"Tocantins"};
const int = new Intl.NumberFormat(locale);
const decimal = new Intl.NumberFormat(locale, {minimumFractionDigits:2, maximumFractionDigits:2});
const ordered = new Intl.Collator("pt-BR", {numeric:true, sensitivity:"base"});
const titleCase = (s) => s.toLocaleLowerCase("pt-BR").replace(
  /(^|[^\p{L}])([\p{L}]+)/gu, (match, prefix, word, offset) =>
    prefix + (offset && ["de","do","da","das","dos","e"].includes(word) ? word : word[0].toUpperCase() + word.slice(1))
);
const html = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const n = (x) => x == null ? "—" : int.format(x);
const rate = (a, b) => b > 0 && a != null ? 100 * a / b : null;
const pct = (x) => x == null ? "—" : decimal.format(x) + "%";
const delta = (a, b) => a == null || b == null ? null : a - b;
const relativeChange = (focus, reference) => reference > 0 && focus != null ?
  100 * (focus - reference) / reference : null;
const signed = (x, unit = "") => {
  if (x == null) return "—";
  const rounded = unit ? Math.round(Math.abs(x) * 100) / 100 : Math.abs(x);
  return (rounded ? (x > 0 ? "+" : "−") : "") +
    (unit ? decimal.format(rounded) + unit : int.format(rounded));
};
const pointsUnit = t(" p.p.", " pp");
const relativeLabel = t("Diferença %", "Change %");
const relativeNote = t(
  "Em Eleitorado e apuração, a Diferença % divide a mudança da taxa pela taxa de referência. A variação fica indisponível se a taxa de referência for zero ou estiver ausente.",
  "For electorate and vote-count indicators, Change % divides the change in the rate by the reference rate. The change is unavailable when the reference rate is zero or missing."
);
const sortLabels = (a, b) => ordered.compare(a[1], b[1]);
const metrics = [
  [t("Aptos", "Eligible voters"), 0, null], [t("Comparecimento", "Turnout"), 1, 0], [t("Abstenção", "Abstention"), 2, 0],
  [t("Votos válidos", "Valid votes"), 3, 1], [t("Brancos", "Blank votes"), 4, 1], [t("Nulos", "Invalid votes"), 5, 1]
];
const files = new Map();
const rjMunicipalPacks = new Map();
const rjReleaseByPack = new WeakMap();
let catalog, geography, geoTask = Promise.resolve(), geoRevision = 0, runRevision = 0;
let visibleReport = null;

function options(select, entries, placeholder, selected = "") {
  const items = placeholder ? [["", placeholder], ...entries] : entries;
  select.replaceChildren(...items.map(([value, label]) => new Option(label, value)));
  if (items.some(([value]) => value === selected)) select.value = selected;
  select.disabled = !entries.length;
}

function fetchData(path, compressed = false) {
  if (!files.has(path)) {
    const promise = (async () => {
      const response = await fetch(new URL(path + (compressed ? ".b64" : ""), dataRoot));
      if (!response.ok) throw new Error(`HTTP ${response.status} · ${path}`);
      if (!compressed) return response.json();
      const encoded = atob(await response.text());
      const bytes = Uint8Array.from(encoded, (character) => character.charCodeAt(0));
      const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
      return new Response(stream).json();
    })();
    files.set(path, promise);
    promise.catch(() => files.delete(path));
    // Evita reter dados detalhados de todos os estados durante uma sessão longa.
    if (files.size > 24) files.delete(files.keys().next().value);
  }
  return files.get(path);
}

async function detailed(ano, state, city) {
  const pack = catalog.indice[ano]?.[state]?.[city];
  if (pack == null) return null;
  return (await fetchData(`secoes-${ano}-${state}-${pack}.json.gz`, true))[city] || null;
}

function sectionLabel(key) {
  const [zone, number] = key.split(":");
  return t(`Seção ${number} · zona ${zone}`, `Polling section ${number} · zone ${zone}`);
}

function locationLabel(data, key) {
  const [zone, number] = key.split(":");
  const label = data?.l[key]?.[0];
  const name = label ? titleCase(label) : t("Local ", "Polling place ") + number;
  return t(`${name} · zona ${zone} · cód. ${number}`, `${name} · zone ${zone} · code ${number}`);
}

function localKeys(key, records) {
  const zone = key.split(":")[0];
  return records.filter(([section, turns]) =>
    section.split(":")[0] === zone && turns.some((row) => row && `${zone}:${row[0]}` === key)
  );
}

function updateSections(selected = "") {
  const records = Object.entries(geography?.s || {});
  const keys = (local.value ? localKeys(local.value, records) : records).map(([key]) => key);
  options(secao, keys.sort(ordered.compare).map((key) => [key, sectionLabel(key)]), t("Todas as seções", "All polling sections"), selected);
}

function loadCities(selected = "") {
  const cities = Object.entries(catalog.uf[uf.value]).map(([code, name]) => [code, titleCase(name)]);
  cities.sort(sortLabels);
  const rio = uf.value === "RJ";
  if (rio) cities.unshift([municipalList, t("Tabela dos 92 municípios", "Table of 92 municipalities")]);
  options(municipio, cities, rio ? t("Total estadual", "Statewide total") : t("Todos os municípios", "All municipalities"), selected);
}

function loadGeography(location = "", section = "") {
  document.dispatchEvent(new Event("atlas:territorychange"));
  const revision = ++geoRevision;
  geography = null;
  options(local, [], t("Selecione um município", "Select a municipality"));
  options(secao, [], t("Selecione um município", "Select a municipality"));
  geoHint.textContent = t("Escolha até o nível que deseja consultar. Pare na UF para ver o estado inteiro.", "Choose the level you want to explore. Select only a state to see statewide results.");
  if (!municipio.value || municipio.value === municipalList) {
    geoTask = Promise.resolve();
    return geoTask;
  }
  const state = uf.value;
  const city = municipio.value;
  geoHint.textContent = t("Carregando locais e seções…", "Loading polling places and sections…");
  geoTask = detailed(year, state, city).then((data) => {
    if (revision !== geoRevision) return;
    geography = data;
    const keys = new Set();
    for (const [key, rows] of Object.entries(data?.s || {})) {
      const zone = key.split(":")[0];
      for (const row of rows) if (row?.[0] > 0) keys.add(`${zone}:${row[0]}`);
    }
    options(local, [...keys].map((key) => [key, locationLabel(data, key)]).sort(sortLabels),
      t("Todos os locais", "All polling places"), location);
    updateSections(section);
    geoHint.textContent = data
      ? t("Os locais e seções listados têm registro de apuração em 2026. Você também pode escolher uma seção diretamente.", "The listed polling places and sections have 2026 results. You can also select a section directly.")
      : t("A base de 2026 não tem registro por seção para este município.", "The 2026 data contain no section-level results for this municipality.");
  }).catch(() => {
    if (revision !== geoRevision) return;
    geoHint.textContent = t("Falha ao carregar locais e seções. Selecione o município novamente ou recarregue a página.", "Could not load polling places and sections. Select the municipality again or reload the page.");
  });
  return geoTask;
}

function updateMode() {
  const compare = form.elements.mode.value === "comparar";
  $("analysis-field").hidden = compare;
  $("compare-field").hidden = !compare;
  $("year-field").hidden = !compare || $("comparacao").value === "turnos";
}

function selection() {
  const list = municipio.value === municipalList;
  return {uf: uf.value, municipio: list ? "" : municipio.value, visao: list ? "municipios" : "",
    local: local.value, secao: secao.value,
    mode: form.elements.mode.value, turno: $("turno").value,
    comparacao: $("comparacao").value, ano: $("ano").value};
}

function urlFor(sel, page = location.href) {
  const link = new URL(page);
  link.search = "";
  link.hash = "";
  for (const key of ["uf", "municipio", "local", "secao", "mode", "visao"]) {
    if (sel[key]) link.searchParams.set(key, sel[key]);
  }
  if (sel.mode === "analisar") link.searchParams.set("turno", sel.turno);
  else {
    link.searchParams.set("comparacao", sel.comparacao);
    if (sel.comparacao !== "turnos") link.searchParams.set("ano", sel.ano);
  }
  return link;
}

function updateLanguageLink() {
  const link = urlFor(selection(), alternatePage);
  link.hash = location.hash;
  languageSwitch.href = link.href;
}

function periods(sel) {
  if (sel.mode === "analisar") return [[year, +sel.turno]];
  if (sel.comparacao === "turnos") return [[year, 2], [year, 1]];
  const turn = sel.comparacao === "historico1" ? 1 : 2;
  return [[year, turn], [+sel.ano, turn]];
}

const periodLabel = ([ano, turno]) =>
  t(`${ano} · ${turno}º turno`, `${ano} · ${turno === 1 ? "First" : "Second"} round`);

function decodeDetail(rows, order) {
  if (!rows.length) return null;
  const values = Array(6).fill(0);
  const counts = Array(order.length).fill(0);
  const incomplete = rows.some((row) => row.length !== order.length + 7);
  for (const row of rows) {
    for (let i = 0; i < values.length; i++) {
      values[i] = values[i] == null || row[i + 1] == null ? null : values[i] + row[i + 1];
    }
    if (!incomplete) for (let i = 0; i < counts.length; i++) counts[i] += row[i + 7];
  }
  return {values, votes: incomplete ? null : Object.fromEntries(order.map((id, i) => [id, counts[i]]))};
}

function loadRjMunicipalPack(ano) {
  if (!rjMunicipalPacks.has(ano)) {
    const path = `${ano}/presidente/RJ/municipios.json`;
    const pending = (async () => {
      try {
        const {release} = await fetchData("r2-rj-release.json");
        if (/^[a-f0-9]{40}-[0-9]+-[0-9]+$/.test(release)) {
          const response = await fetch(
            "https://atlas-data.electoralintegrity.org/releases/" + release + "/" + path,
            {signal: AbortSignal.timeout(3500)}
          );
          if (response.ok) {
            const data = await response.json();
            const records = data.registros;
            if (data.schema === 1 && data.ano === ano && data.cargo === "presidente" &&
                data.uf === "RJ" && records?.[""] && Object.keys(records).length === 93 &&
                Object.values(records).every(turns =>
                  Array.isArray(turns?.[1]) && Array.isArray(turns?.[2]))) {
              rjReleaseByPack.set(records, release);
              return records;
            }
          }
        }
      } catch {
        // A rede, o CORS ou um desafio do Cloudflare podem bloquear a leitura pública.
      }
      return (await fetchData(path)).registros;
    })();
    rjMunicipalPacks.set(ano, pending);
    pending.catch(() => rjMunicipalPacks.delete(ano));
  }
  return rjMunicipalPacks.get(ano);
}

async function loadMunicipalPack(ano, state) {
  if (state === "RJ") return loadRjMunicipalPack(ano);
  return fetchData(`municipios-${ano}-${state}.json.gz`, true);
}

function municipalResult(pack, city, turn) {
  const row = pack[city]?.[turn];
  return row ? {values: row.slice(0, 6), votes: Object.fromEntries(row.slice(6))} : null;
}

async function loadResult(sel, [ano, turno]) {
  if (!sel.local && !sel.secao) {
    return municipalResult(await loadMunicipalPack(ano, sel.uf), sel.municipio, turno);
  }
  const pack = await detailed(ano, sel.uf, sel.municipio);
  if (!pack) return null;
  if (sel.secao) {
    const row = pack.s[sel.secao]?.[turno - 1];
    if (!row) return null;
    const loc = `${sel.secao.split(":")[0]}:${row[0]}`;
    return {...decodeDetail([row], catalog.anos[ano].ordem), sectionKeys: [sel.secao],
      loc, locationName: pack.l[loc]?.[0], address: pack.l[loc]?.[1]};
  }
  const keys = localKeys(sel.local, Object.entries(pack.s))
    .filter(([key, turns]) => turns[turno - 1]?.[0] === +sel.local.split(":")[1])
    .map(([key]) => key);
  const decoded = decodeDetail(keys.map((key) => pack.s[key][turno - 1]), catalog.anos[ano].ordem);
  return decoded ? {...decoded, sectionKeys: keys, loc: sel.local, locationName: pack.l[sel.local]?.[0],
    address: pack.l[sel.local]?.[1]} : null;
}

function candidateRows(periodList, results) {
  const people = new Map();
  periodList.forEach(([ano, turno], i) => {
    const data = catalog.anos[ano];
    for (const code of data.turnos[turno]) {
      const [short, full] = data.candidatos[code];
      const identity = full.normalize("NFD").replace(/\p{Diacritic}/gu, "").trim().replace(/\s+/g, " ").toUpperCase();
      if (!people.has(identity)) people.set(identity, {name: titleCase(short), votes: [null, null]});
      const current = results[i];
      if (current?.votes) people.get(identity).votes[i] = current.votes[code] || 0;
    }
  });
  return [...people.entries()].map(([identity, {name, votes}]) => ({
    key: "c:" + identity, name, votes, rates: votes.map((value, i) => rate(value, results[i]?.values[3]))
  })).sort((a, b) => (b.votes[0] ?? -1) - (a.votes[0] ?? -1) ||
    (b.votes[1] ?? -1) - (a.votes[1] ?? -1) || ordered.compare(a.name, b.name));
}

function metricRows(results) {
  const rows = metrics.map(([name, idx, divisor]) => ({
    key: "m:" + idx, name, votes: [0, 1].map((i) => results[i]?.values[idx] ?? null),
    rates: [0, 1].map((i) => divisor == null ? null : rate(results[i]?.values[idx], results[i]?.values[divisor]))
  }));
  const other = [0, 1].map((i) => {
    const values = results[i]?.values;
    return values && results[i].votes ? values[1] - values[3] - values[4] - values[5] : null;
  });
  if (other.some((value) => value)) rows.push({
    key: "m:other", name:t("Outras categorias da apuração", "Other count categories"), votes:other,
    rates:other.map((value, i) => rate(value, results[i]?.values[1]))
  });
  return rows;
}

function countWithRate(count, formattedRate) {
  return `${count}${formattedRate === "—" ? "" : ` <span class="paired-rate">(${formattedRate})</span>`}`;
}

function table(name, rows, labels, type, indicators = [], relative = false) {
  const comparing = labels.length === 2;
  const changeLabel = relative ? relativeLabel : t("Diferença", "Change");
  const changeDetail = indicators.length ? t("Quantidade e variação da taxa", "Count and change in rate") :
    relative ? t("Quantidade (variação %)", "Count (% change)") : t("Quantidade (p.p.)", "Count (pp)");
  const head = `<tr><th scope="col">${type}</th>${labels.map((label) =>
    comparing ? `<th scope="col">${label}<br>${t("Quantidade (%)", "Count (%)")}</th>` :
      `<th scope="col">${label}<br>${t("Quantidade", "Count")}</th><th scope="col">${label}<br>${t("Taxa", "Rate")}</th>`).join("")}
    ${comparing ? `<th scope="col">${changeLabel}<br>${changeDetail}</th>` : ""}</tr>`;
  const renderRows = (items, relativeRates) => items.map(({name, votes, rates}) =>
    `<tr><th scope="row">${html(name)}</th>${labels.map((_, i) =>
      comparing ? `<td class="paired-count">${countWithRate(n(votes[i]), pct(rates[i]))}</td>` :
        `<td>${n(votes[i])}</td><td>${pct(rates[i])}</td>`).join("")}
    ${comparing ? `<td class="paired-count">${countWithRate(signed(delta(...votes)),
      relativeRates ? signed(relativeChange(...rates), "%") : signed(delta(...rates), pointsUnit))}</td>` : ""}</tr>`
  ).join("");
  const totals = indicators.length ?
    `<tbody><tr class="table-group"><th scope="rowgroup" colspan="3">${t("Eleitorado e apuração", "Electorate and vote count")}</th>
      <th>${relativeLabel}</th></tr>${renderRows(indicators, true)}</tbody>` : "";
  return `<section class="panel table-panel"><h3>${name}</h3><div class="table-wrap" tabindex="0" role="region" aria-label="${name}"><table><thead>${head}</thead><tbody>${renderRows(rows, relative)}</tbody>${totals}</table></div></section>`;
}

function chart(rows, labels) {
  const top = rows.filter((row) => row.rates.some((value) => value > 0)).slice(0, 6);
  if (!top.length) return "";
  const comparing = labels.length === 2;
  return `<section class="panel chart"><div class="chart-head"><h3>${t("Participação nos votos válidos", "Share of valid votes")}</h3>
    <div class="legend">${labels.map((label, i) => `<span><i class="${i ? "base" : "focus"}-key"></i>${label}</span>`).join("")}</div></div>
    ${top.map(({name, votes, rates}) => `<div class="chart-row"><strong>${html(name)}</strong><div>${labels.map((label, i) => {
      const value = comparing ? countWithRate(n(votes[i]), pct(rates[i])) : pct(rates[i]);
      return `<div class="bar-line${comparing ? " bar-line-compare" : ""}"><span class="track" aria-hidden="true">
      <i class="${i ? "base" : "focus"}-bar" style="width:${Math.min(100, rates[i] || 0)}%"></i></span><span><span class="sr-only">${label}: </span>${value}</span></div>`;
    }).join("")}</div></div>`).join("")}</section>`;
}

function cards(rows, labels) {
  const comparing = labels.length === 2;
  return `<div class="metrics">${[0, 1, 3].map((idx) => {
    const {name, votes, rates} = rows[idx];
    const change = idx === 1 ? signed(relativeChange(...rates), "%") : signed(delta(...votes));
    const reference = t(`${n(votes[1])} na referência · diferença ${change}`, `${n(votes[1])} in the reference period · change ${change}`);
    return `<div class="panel metric"><span>${name}</span><b>${n(votes[0])}</b><small>${comparing ? reference : (idx ? pct(rates[0]) : labels[0])}</small></div>`;
  }).join("")}</div>`;
}

function territory(sel) {
  const city = catalog.uf[sel.uf]?.[sel.municipio];
  const trail = [sel.uf, city && titleCase(city)].filter(Boolean);
  if (sel.local && !sel.secao) trail.push(t("Local de votação", "Polling place"));
  if (sel.secao) trail.push(t("Seção eleitoral", "Polling section"));
  const name = sel.visao ? t("92 municípios do Rio de Janeiro", "92 municipalities of Rio de Janeiro") :
    sel.secao ? sectionLabel(sel.secao) : sel.local ? locationLabel(geography, sel.local) :
    city ? titleCase(city) : states[sel.uf];
  return {name, trail: trail.join(" / ")};
}

function show(sel, periodList, results) {
  const labels = periodList.map(periodLabel);
  const notes = [];
  results.forEach((result, i) => {
    if (!result) notes.push(t(`Sem registro para este recorte em ${labels[i]}.`, `No data for this area in ${labels[i]}.`));
    else if (!result.votes) notes.push(t(`Em ${labels[i]}, a soma nominal diverge do detalhe da apuração em pelo menos uma seção deste recorte. O painel exibe os totais de apuração e omite a distribuição por candidato para esse período.`, `In ${labels[i]}, the sum of votes by candidate differs from the detailed count in at least one section in this area. Only vote-count totals are shown for that period.`));
  });
  if (results[0]?.sectionKeys && results[1]?.sectionKeys) {
    const [a, b] = results;
    if (a.loc !== b.loc) notes.push(t("A seção aparece em locais de votação diferentes nos dois períodos.", "The section is listed under different polling places in the two periods."));
    if (a.locationName && b.locationName && a.locationName !== b.locationName) {
      notes.push(t("O nome do local consta de forma diferente nos dois períodos. Confira a correspondência territorial antes de interpretar as diferenças.", "The polling place is listed under different names in the two periods. Check that the locations correspond before interpreting the differences."));
    }
    if (a.sectionKeys.length !== b.sectionKeys.length || a.sectionKeys.some((key) => !b.sectionKeys.includes(key))) {
      notes.push(t(`O local reúne conjuntos diferentes de seções: ${a.sectionKeys.length} no período em foco e ${b.sectionKeys.length} na referência.`, `This polling place covers different sets of sections: ${a.sectionKeys.length} in the focus period and ${b.sectionKeys.length} in the reference period.`));
    }
  }
  const candidates = candidateRows(periodList, results);
  const indicators = metricRows(results);
  const found = results.some(Boolean);
  const nominal = results.some((result) => result?.votes);
  const notices = notes.map((note) => `<p class="notice">${html(note)}</p>`).join("");
  const bars = nominal ? chart(candidates, labels) : "";
  const resultsPanels = labels.length === 2 ?
    table(t("Comparação de resultados", "Results comparison"), nominal ? candidates : indicators, labels, t("Indicador", "Indicator"), nominal ? indicators : [], !nominal) + bars :
    bars + (nominal ? table(t("Votação nominal", "Votes by candidate"), candidates, labels, t("Candidatura", "Candidate")) : "") +
    table(t("Eleitorado e apuração", "Electorate and vote count"), indicators, labels, t("Indicador", "Indicator"));
  $("output").innerHTML = notices + (found ?
    cards(indicators, labels) + resultsPanels +
    `<p class="hint">${t(
      "Taxas de candidatos sobre válidos. Comparecimento e abstenção sobre aptos. Válidos, brancos e nulos sobre comparecimento. O traço indica dado indisponível ou candidatura ausente no turno.",
      "Candidate shares use valid votes. Turnout and abstention use eligible voters. Valid, blank and invalid vote rates use turnout. A dash indicates unavailable data or a candidate absent from the round."
    )}</p>${labels.length === 2 ? `<p class="hint">${relativeNote}</p>` : ""}` : "");
  if (results[0]?.address) $("subtitle").textContent += " · " + titleCase(results[0].address);
  visibleReport = found ? {sel, labels, indicators, candidates: nominal ? candidates : []} : null;
  $("actions").hidden = !found;
  $("status").textContent = found ? "" : t("Nenhum resultado disponível para a consulta.", "No results available for this query.");
}

function showMunicipalities(sel, periodList, packs) {
  const resultsFor = (code) => periodList.map(([, turn], i) => municipalResult(packs[i], code, turn));
  const state = resultsFor("");
  const candidates = candidateRows(periodList, state);
  const indicators = metricRows(state);
  const labels = periodList.map(periodLabel);
  const comparing = labels.length === 2;
  const overview = Object.entries(catalog.uf[sel.uf]).map(([code, rawName]) => {
    const name = titleCase(rawName);
    const results = resultsFor(code);
    const url = urlFor({...sel, visao: "", municipio: code});
    url.hash = "resultado";
    return {code, name, url, candidates: candidateRows(periodList, results), indicators: metricRows(results)};
  }).sort((a, b) => ordered.compare(a.name, b.name));
  const heading = t("Resultados por município", "Results by municipality");
  const municipality = t("Município", "Municipality");
  const change = comparing ? '<th scope="col" id="municipal-change"></th>' : "";
  $("output").innerHTML = `<section class="panel table-panel" aria-labelledby="municipal-heading">
    <h3 id="municipal-heading">${heading}</h3>
    <p class="hint">${t("Escolha um candidato ou indicador. Abra um município para ver o resultado completo. O CSV inclui todos os municípios, candidatos e indicadores.", "Choose a candidate or an indicator. Open a municipality to view its full results. The CSV includes all municipalities, candidates and indicators.")}</p>
    <div class="municipal-controls fields">
      <label>${t("Candidato ou indicador", "Candidate or indicator")}<select id="municipal-indicator"></select></label>
      <label>${t("Ordenar por", "Sort by")}<select id="municipal-sort"></select></label>
    </div>
    <div class="table-wrap" tabindex="0" role="region" aria-label="${heading}">
      <table><thead><tr><th scope="col">${municipality}</th>
        ${labels.map((label) => `<th scope="col">${label}<br>${t("Quantidade (%)", "Count (%)")}</th>`).join("")}
        ${change}</tr></thead><tbody id="municipal-rows"></tbody></table>
    </div>
    <p class="hint">${t("Candidatos sobre votos válidos. Comparecimento e abstenção sobre aptos. Válidos, brancos e nulos sobre comparecimento. O traço indica dado indisponível ou candidatura ausente no turno.", "Candidate shares use valid votes. Turnout and abstention use eligible voters. Valid, blank and invalid vote rates use turnout. A dash indicates unavailable data or a candidate absent from the round.")}</p>
    ${comparing ? `<p class="hint">${relativeNote}</p>` : ""}
  </section>`;
  const indicator = $("municipal-indicator");
  const sort = $("municipal-sort");
  options(indicator, [...candidates, ...indicators].map(({key, name}) => [key, name]));
  options(sort, [
    ["name", t("Município (A–Z)", "Municipality (A–Z)")],
    ["count", t("Maior quantidade no período em foco", "Highest count in focus period")],
    ["rate", t("Maior percentual no período em foco", "Highest percentage in focus period")],
    ...(comparing ? [
      ["count-change", t("Maior aumento em quantidade", "Largest increase in count")],
      ["rate-change", t("Maior aumento na taxa", "Largest increase in rate")]
    ] : [])
  ]);
  const sortValue = {
    count: ({votes}) => votes[0],
    rate: ({rates}) => rates[0],
    "count-change": ({votes}) => delta(...votes)
  };
  function renderRows() {
    const relative = indicator.value.startsWith("m:");
    const rateChange = relative ? relativeChange : delta;
    if (comparing) $("municipal-change").textContent = relative ? relativeLabel : t("Diferença (p.p.)", "Change (pp)");
    const rows = overview.map(({name, url, candidates, indicators}) => {
      const row = [...candidates, ...indicators].find(({key}) => key === indicator.value);
      return {name, url, votes: row?.votes || [], rates: row?.rates || []};
    });
    const value = sort.value === "rate-change" ? ({rates}) => rateChange(...rates) : sortValue[sort.value];
    if (value) rows.sort((a, b) => (value(b) ?? -Infinity) - (value(a) ?? -Infinity));
    $("municipal-rows").innerHTML = rows.map(({name, url, votes, rates}) => `<tr>
      <th scope="row"><a href="${html(url.href)}">${html(name)}</a></th>
      ${labels.map((_, i) => `<td class="paired-count">${countWithRate(n(votes[i]), pct(rates[i]))}</td>`).join("")}
      ${comparing ? `<td class="paired-count">${countWithRate(signed(delta(...votes)),
        signed(rateChange(...rates), relative ? "%" : pointsUnit))}</td>` : ""}</tr>`).join("");
  }
  indicator.addEventListener("change", renderRows);
  sort.addEventListener("change", renderRows);
  renderRows();
  visibleReport = {sel, labels, overview};
  $("actions").hidden = false;
  $("status").textContent = "";
}

async function run(focus = false) {
  const revision = ++runRevision;
  await geoTask;
  if (revision !== runRevision) return;
  const sel = selection();
  const periodList = periods(sel);
  const place = territory(sel);
  const labels = periodList.map(periodLabel);
  $("breadcrumb").textContent = place.trail;
  $("resultado-titulo").textContent = place.name;
  $("subtitle").textContent = labels.length === 2 ? t(`Foco: ${labels[0]} · Referência: ${labels[1]}`, `Focus: ${labels[0]} · Reference: ${labels[1]}`) : labels[0];
  $("status").textContent = t("Carregando os resultados…", "Loading results…");
  $("output").replaceChildren();
  $("actions").hidden = true;
  visibleReport = null;
  if (focus) $("resultado-titulo").focus();
  try {
    if (sel.visao) {
      const packs = await Promise.all(periodList.map(([ano]) => loadMunicipalPack(ano, sel.uf)));
      if (revision !== runRevision) return;
      showMunicipalities(sel, periodList, packs);
    } else {
      const results = await Promise.all(periodList.map((period) => loadResult(sel, period)));
      if (revision !== runRevision) return;
      show(sel, periodList, results);
    }
    const resultUrl = urlFor(sel);
    resultUrl.hash = location.hash;
    history.replaceState(null, "", resultUrl);
    updateLanguageLink();
  } catch {
    if (revision === runRevision) $("status").textContent = t("Falha ao carregar os resultados. Tente novamente.", "Could not load the results. Try again.");
  }
}

function csv() {
  if (!visibleReport) return;
  const {sel, labels, overview} = visibleReport;
  const compare = labels.length === 2;
  const context = [sel.uf, sel.municipio, sel.local, sel.secao];
  const header = [t("UF", "State"), t("Município TSE", "Municipality (TSE code)"),
    ...(overview ? [t("Município", "Municipality")] : []),
    t("Local (zona:código)", "Polling place (zone:code)"), t("Seção (zona:número)", "Polling section (zone:number)"), t("Tipo", "Type"), t("Indicador", "Indicator"),
    ...labels.flatMap((label) => [label + t(" quantidade", " count"), label + t(" taxa (%)", " rate (%)")]),
    ...(compare ? [t("Diferença", "Change"), t("Diferença (p.p.)", "Change (pp)"), relativeLabel] : [])];
  const rows = [header];
  for (const report of overview || [visibleReport]) {
    const area = overview ? [sel.uf, report.code, report.name, "", ""] : context;
    for (const [kind, list, relative] of [
      [t("Apuração", "Vote count"), report.indicators, true], [t("Candidato", "Candidate"), report.candidates, false]
    ]) {
      for (const {name, votes, rates} of list) rows.push([...area, kind, name,
        ...labels.flatMap((_, i) => [votes[i], csvNumber(rates[i])]),
        ...(compare ? [delta(...votes), relative ? "" : csvNumber(delta(...rates)),
          relative ? csvNumber(relativeChange(...rates)) : ""] : [])]);
    }
  }
  const fileArea = overview ? `${sel.uf}-municipios-${periods(sel).flat().join("-")}` : context.filter(Boolean).join("-").replaceAll(":", "-");
  downloadCsv(rows, `atlas-${fileArea}.csv`);
}

function csvNumber(value) {
  if (value == null) return "";
  const fixed = value.toFixed(2);
  return english ? fixed : fixed.replace(".", ",");
}

function downloadCsv(rows, filename) {
  const cell = (value) => '"' + String(value ?? "").replaceAll('"', '""') + '"';
  const file = new Blob(["\uFEFF", rows.map((row) => row.map(cell).join(t(";", ","))).join("\r\n")],
    {type:"text/csv;charset=utf-8"});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(file);
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

async function start() {
  const params = new URLSearchParams(location.search);
  const initialAlternate = new URL(alternatePage);
  initialAlternate.search = location.search;
  initialAlternate.hash = location.hash;
  languageSwitch.href = initialAlternate.href;
  form.querySelector('button[type="submit"]').disabled = true;
  options(uf, [], t("Carregando…", "Loading…"));
  try {
    catalog = await fetchData("catalogo.json");
  } catch {
    $("status").textContent = t("Não foi possível abrir o catálogo eleitoral. Recarregue a página para tentar novamente.", "Could not load the election catalogue. Reload the page to try again.");
    return;
  }
  options(uf, Object.keys(catalog.uf).map((code) => [code, `${code} · ${states[code]}`]),
    null, params.get("uf") || "RJ");
  for (const id of ["turno", "comparacao", "ano"]) {
    const select = $(id);
    if ([...select.options].some(({value}) => value === params.get(id))) select.value = params.get(id);
  }
  if (params.get("mode") === "comparar") form.elements.mode.value = "comparar";
  const city = uf.value === "RJ" && params.get("visao") === "municipios" ? municipalList : params.get("municipio");
  loadCities(city || "");
  updateMode();
  loadGeography(params.get("local") || "", params.get("secao") || "");
  uf.addEventListener("change", () => { loadCities(); loadGeography(); });
  municipio.addEventListener("change", () => loadGeography());
  local.addEventListener("change", () => updateSections());
  form.addEventListener("change", async () => {
    updateMode();
    updateLanguageLink();
    await geoTask;
    updateLanguageLink();
  });
  window.addEventListener("hashchange", updateLanguageLink);
  form.addEventListener("submit", (event) => { event.preventDefault(); run(true); });
  document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", () => {
    const [state, city] = button.dataset.preset.split(":");
    uf.value = state;
    if (city === municipalList) {
      form.elements.mode.value = "comparar";
      $("comparacao").value = "turnos";
      updateMode();
    }
    loadCities(city);
    loadGeography();
    run(true);
  }));
  $("csv").addEventListener("click", csv);
  $("share").addEventListener("click", async () => {
    if (!visibleReport) return;
    const link = urlFor(visibleReport.sel).href;
    try {
      await navigator.clipboard.writeText(link);
      $("status").textContent = t("Link da consulta copiado.", "Query link copied.");
    } catch {
      window.prompt(t("Copie o link da consulta", "Copy the query link"), link);
    }
  });
  form.querySelector('button[type="submit"]').disabled = false;
  await geoTask;
  updateLanguageLink();
  run();
}

const atlasExplorerReady = start();

const atlasChatExplorer = {
  async context() {
    await atlasExplorerReady;
    if (!catalog) throw new Error("Missing Atlas catalogue");
    return selection();
  },

  get catalogue() {
    return {states, cities: catalog.uf, years: catalog.anos};
  },

  workerResult(answer) {
    const {filters, periods: availablePeriods, table, notes, sources} = answer;
    const labels = availablePeriods.map(({ano, turno}) => periodLabel([ano, turno]));
    const area = [
      states[filters.uf],
      filters.municipio && titleCase(catalog.uf[filters.uf][filters.municipio]),
      filters.local && t("Local de votação ", "Polling place ") + filters.local,
      filters.secao && sectionLabel(filters.secao)
    ].filter(Boolean).join(" · ");
    const link = urlFor(filters);
    link.hash = "explorador";
    const versions = new Map();
    for (const {url} of sources) {
      const path = new URL(url).pathname;
      const match = path.match(/^\/releases\/([^/]+)\/(\d{4})\/presidente\/RJ\/municipios\.json$/);
      if (!match) continue;
      const [, release, releaseYear] = match;
      if (!versions.has(release)) versions.set(release, []);
      versions.get(release).push(releaseYear);
    }
    const rows = table.map(row => {
      const metric = metrics.find(([, code]) => row.key === "m:" + code);
      return {
        name:metric?.[0] ?? row.name,
        values:labels.map((_, i) => [n(row.counts[i]), pct(row.rates[i])]),
        difference:[signed(row.countDelta), signed(row.rateDelta, row.rateDeltaUnit === "pp" ? pointsUnit : "%")]
      };
    });
    return {
      area, rows, labels, link:link.href, source:new URL("fontes.json", dataRoot).href,
      gaps:availablePeriods.flatMap(({available}, i) => available ? [] : [labels[i]]),
      notes:english ? [] : notes,
      versions:[...versions]
    };
  },

  async result(filters, metric) {
    if (!filters || typeof filters !== "object") throw new Error("Missing filters");
    const {uf, municipio = "", local = "", secao = "", mode = "analisar",
      turno = "2", comparacao = "turnos", ano = "2022"} = filters;
    const own = (object, key) => Object.hasOwn(object, key);
    if (typeof uf !== "string" || !own(catalog.uf, uf) ||
        typeof municipio !== "string" || (municipio && !own(catalog.uf[uf], municipio)) ||
        !["analisar", "comparar"].includes(mode) || !["1", "2"].includes(turno) ||
        !["turnos", "historico1", "historico2"].includes(comparacao) ||
        !["2010", "2014", "2018", "2022"].includes(ano) ||
        ![local, secao].every(key => typeof key === "string" && (!key || /^\d+:\d+$/.test(key))) ||
        ((local || secao) && !municipio)) throw new Error("Invalid Atlas filters");

    const sel = {uf, municipio, local, secao, mode, turno, comparacao, ano};
    const periodList = periods(sel);
    const labels = periodList.map(periodLabel);
    const detail = local || secao ? await detailed(year, uf, municipio) : null;
    if ((local && (!detail || !localKeys(local, Object.entries(detail.s)).length)) ||
        (secao && (!detail || !own(detail.s, secao) ||
          (local && !localKeys(local, [[secao, detail.s[secao]]]).length)))) {
      return {gaps:labels, rows:[], selection:sel};
    }
    const area = [states[uf], municipio && titleCase(catalog.uf[uf][municipio]),
      local && locationLabel(detail, local), secao && sectionLabel(secao)].filter(Boolean).join(" · ");
    const results = await Promise.all(periodList.map(period => loadResult(sel, period)));
    const link = urlFor(sel);
    link.hash = "resultado";
    const source = new URL("fontes.json", dataRoot).href;
    const gaps = labels.filter((_, i) => !results[i]);
    const candidateGap = results.some(result => result && !result.votes);
    const versions = new Map();
    if (uf === "RJ" && !detail) {
      for (const periodYear of new Set(periodList.map(([itemYear]) => itemYear))) {
        const release = rjReleaseByPack.get(await loadMunicipalPack(periodYear, uf));
        if (release) {
          if (!versions.has(release)) versions.set(release, []);
          versions.get(release).push(periodYear);
        }
      }
    }
    const rows = [...metricRows(results), ...candidateRows(periodList, results)]
      .filter(row => !metric || row.key === metric)
      .filter(row => row.votes.slice(0, labels.length).some(value => value != null))
      .map(row => {
        const relative = row.key.startsWith("m:");
        const rateDifference = relative ? relativeChange(...row.rates) : delta(...row.rates);
        return {name:row.name, values:labels.map((_, i) => [n(row.votes[i]), pct(row.rates[i])]),
          difference:[signed(delta(...row.votes)), signed(rateDifference, relative ? "%" : pointsUnit)]};
      });
    return {area, rows, labels, link:link.href, source, gaps, candidateGap, versions:[...versions], selection:sel};
  }
};
