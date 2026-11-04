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
const signed = (x, points = false) => {
  if (x == null) return "—";
  const rounded = points ? Math.round(Math.abs(x) * 100) / 100 : Math.abs(x);
  return (rounded ? (x > 0 ? "+" : "−") : "") +
    (points ? decimal.format(rounded) + t(" p.p.", " pp") : int.format(rounded));
};
const sortLabels = (a, b) => ordered.compare(a[1], b[1]);
const metrics = [
  [t("Aptos", "Eligible voters"), 0, null], [t("Comparecimento", "Turnout"), 1, 0], [t("Abstenção", "Abstention"), 2, 0],
  [t("Votos válidos", "Valid votes"), 3, 1], [t("Brancos", "Blank votes"), 4, 1], [t("Nulos", "Invalid votes"), 5, 1]
];
const files = new Map();
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
  options(municipio, cities.sort(sortLabels), t("Todos os municípios", "All municipalities"), selected);
}

function loadGeography(location = "", section = "") {
  const revision = ++geoRevision;
  geography = null;
  options(local, [], t("Selecione um município", "Select a municipality"));
  options(secao, [], t("Selecione um município", "Select a municipality"));
  geoHint.textContent = t("Escolha até o nível que deseja consultar. Pare na UF para ver o estado inteiro.", "Choose the level you want to explore. Select only a state to see statewide results.");
  if (!municipio.value) {
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
  return {uf: uf.value, municipio: municipio.value, local: local.value, secao: secao.value,
    mode: form.elements.mode.value, turno: $("turno").value,
    comparacao: $("comparacao").value, ano: $("ano").value};
}

function urlFor(sel, page = location.href) {
  const link = new URL(page);
  link.search = "";
  link.hash = "";
  for (const key of ["uf", "municipio", "local", "secao", "mode"]) {
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

async function loadResult(sel, [ano, turno]) {
  if (!sel.local && !sel.secao) {
    const pack = await fetchData(`municipios-${ano}-${sel.uf}.json.gz`, true);
    const row = pack[sel.municipio]?.[turno];
    return row ? {values: row.slice(0, 6), votes: Object.fromEntries(row.slice(6))} : null;
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
  return [...people.values()].map(({name, votes}) => ({
    name, votes, rates: votes.map((value, i) => rate(value, results[i]?.values[3]))
  })).sort((a, b) => (b.votes[0] ?? -1) - (a.votes[0] ?? -1) ||
    (b.votes[1] ?? -1) - (a.votes[1] ?? -1) || ordered.compare(a.name, b.name));
}

function metricRows(results) {
  const rows = metrics.map(([name, idx, divisor]) => ({
    name, votes: [0, 1].map((i) => results[i]?.values[idx] ?? null),
    rates: [0, 1].map((i) => divisor == null ? null : rate(results[i]?.values[idx], results[i]?.values[divisor]))
  }));
  const other = [0, 1].map((i) => {
    const values = results[i]?.values;
    return values && results[i].votes ? values[1] - values[3] - values[4] - values[5] : null;
  });
  if (other.some((value) => value)) rows.push({
    name:t("Outras categorias da apuração", "Other count categories"), votes:other,
    rates:other.map((value, i) => rate(value, results[i]?.values[1]))
  });
  return rows;
}

function countWithRate(count, formattedRate) {
  return `${count}${formattedRate === "—" ? "" : ` <span class="paired-rate">(${formattedRate})</span>`}`;
}

function table(name, rows, labels, type, indicators = []) {
  const comparing = labels.length === 2;
  const head = `<tr><th scope="col">${type}</th>${labels.map((label) =>
    comparing ? `<th scope="col">${label}<br>${t("Quantidade (%)", "Count (%)")}</th>` :
      `<th scope="col">${label}<br>${t("Quantidade", "Count")}</th><th scope="col">${label}<br>${t("Taxa", "Rate")}</th>`).join("")}
    ${comparing ? `<th scope="col">${t("Diferença", "Change")}<br>${t("Quantidade (p.p.)", "Count (pp)")}</th>` : ""}</tr>`;
  const renderRows = (items) => items.map(({name, votes, rates}) =>
    `<tr><th scope="row">${html(name)}</th>${labels.map((_, i) =>
      comparing ? `<td class="paired-count">${countWithRate(n(votes[i]), pct(rates[i]))}</td>` :
        `<td>${n(votes[i])}</td><td>${pct(rates[i])}</td>`).join("")}
    ${comparing ? `<td class="paired-count">${countWithRate(signed(delta(...votes)), signed(delta(...rates), true))}</td>` : ""}</tr>`
  ).join("");
  const totals = indicators.length ?
    `<tbody><tr class="table-group"><th scope="rowgroup" colspan="4">${t("Eleitorado e apuração", "Electorate and vote count")}</th></tr>${renderRows(indicators)}</tbody>` : "";
  return `<section class="panel table-panel"><h3>${name}</h3><div class="table-wrap" tabindex="0" role="region" aria-label="${name}"><table><thead>${head}</thead><tbody>${renderRows(rows)}</tbody>${totals}</table></div></section>`;
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
    const change = idx === 1 ? signed(delta(...rates), true) : signed(delta(...votes));
    const reference = t(`${n(votes[1])} na referência · diferença ${change}`, `${n(votes[1])} in the reference period · change ${change}`);
    return `<div class="panel metric"><span>${name}</span><b>${n(votes[0])}</b><small>${comparing ? reference : (idx ? pct(rates[0]) : labels[0])}</small></div>`;
  }).join("")}</div>`;
}

function territory(sel) {
  const city = catalog.uf[sel.uf]?.[sel.municipio];
  const trail = [sel.uf, city && titleCase(city)].filter(Boolean);
  if (sel.local && !sel.secao) trail.push(t("Local de votação", "Polling place"));
  if (sel.secao) trail.push(t("Seção eleitoral", "Polling section"));
  const name = sel.secao ? sectionLabel(sel.secao) : sel.local ? locationLabel(geography, sel.local) :
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
    table(t("Comparação de resultados", "Results comparison"), nominal ? candidates : indicators, labels, t("Indicador", "Indicator"), nominal ? indicators : []) + bars :
    bars + (nominal ? table(t("Votação nominal", "Votes by candidate"), candidates, labels, t("Candidatura", "Candidate")) : "") +
    table(t("Eleitorado e apuração", "Electorate and vote count"), indicators, labels, t("Indicador", "Indicator"));
  $("output").innerHTML = notices + (found ?
    cards(indicators, labels) + resultsPanels +
    `<p class="hint">${t(
      "Taxas de candidatos sobre válidos. Comparecimento e abstenção sobre aptos. Válidos, brancos e nulos sobre comparecimento. O traço indica dado indisponível ou candidatura ausente no turno.",
      "Candidate shares use valid votes. Turnout and abstention use eligible voters. Valid, blank and invalid vote rates use turnout. A dash indicates unavailable data or a candidate absent from the round."
    )}</p>` : "");
  if (results[0]?.address) $("subtitle").textContent += " · " + titleCase(results[0].address);
  visibleReport = found ? {sel, labels, indicators, candidates: nominal ? candidates : []} : null;
  $("actions").hidden = !found;
  $("status").textContent = found ? "" : t("Nenhum resultado disponível para a consulta.", "No results available for this query.");
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
    const results = await Promise.all(periodList.map((period) => loadResult(sel, period)));
    if (revision !== runRevision) return;
    show(sel, periodList, results);
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
  const {sel, labels, indicators, candidates} = visibleReport;
  const compare = labels.length === 2;
  const context = [sel.uf, sel.municipio, sel.local, sel.secao];
  const header = [t("UF", "State"), t("Município TSE", "Municipality (TSE code)"), t("Local (zona:código)", "Polling place (zone:code)"), t("Seção (zona:número)", "Polling section (zone:number)"), t("Tipo", "Type"), t("Indicador", "Indicator"),
    ...labels.flatMap((label) => [label + t(" quantidade", " count"), label + t(" taxa (%)", " rate (%)")]),
    ...(compare ? [t("Diferença", "Change"), t("Diferença (p.p.)", "Change (pp)")] : [])];
  const cell = (value) => '"' + String(value ?? "").replaceAll('"', '""') + '"';
  const num = (value) => {
    if (value == null) return "";
    const fixed = value.toFixed(2);
    return english ? fixed : fixed.replace(".", ",");
  };
  const rows = [header];
  for (const [kind, list] of [[t("Apuração", "Vote count"), indicators], [t("Candidato", "Candidate"), candidates]]) {
    for (const {name, votes, rates} of list) rows.push([...context, kind, name,
      ...labels.flatMap((_, i) => [votes[i], num(rates[i])]),
      ...(compare ? [delta(...votes), num(delta(...rates))] : [])]);
  }
  const file = new Blob(["\uFEFF", rows.map((row) => row.map(cell).join(t(";", ","))).join("\r\n")],
    {type:"text/csv;charset=utf-8"});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(file);
  link.download = `atlas-${context.filter(Boolean).join("-").replaceAll(":", "-")}.csv`;
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
  loadCities(params.get("municipio") || "");
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

start();
