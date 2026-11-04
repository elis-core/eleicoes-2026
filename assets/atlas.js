"use strict";

const $ = (id) => document.getElementById(id);
const form = $("filters");
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
const int = new Intl.NumberFormat("pt-BR");
const decimal = new Intl.NumberFormat("pt-BR", {minimumFractionDigits:2, maximumFractionDigits:2});
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
    (points ? decimal.format(rounded) + " p.p." : int.format(rounded));
};
const sortLabels = (a, b) => ordered.compare(a[1], b[1]);
const metrics = [
  ["Aptos", 0, null], ["Comparecimento", 1, 0], ["Abstenções", 2, 0],
  ["Votos válidos", 3, 1], ["Brancos", 4, 1], ["Nulos", 5, 1]
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
      const response = await fetch("dados/" + path + (compressed ? ".b64" : ""));
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
  return `Seção ${number} · zona ${zone}`;
}

function locationLabel(data, key) {
  const [zone, number] = key.split(":");
  const label = data?.l[key]?.[0];
  return `${label ? titleCase(label) : "Local " + number} · zona ${zone} · cód. ${number}`;
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
  options(secao, keys.sort(ordered.compare).map((key) => [key, sectionLabel(key)]), "Todas as seções", selected);
}

function loadCities(selected = "") {
  const cities = Object.entries(catalog.uf[uf.value]).map(([code, name]) => [code, titleCase(name)]);
  options(municipio, cities.sort(sortLabels), "Todos os municípios", selected);
}

function loadGeography(location = "", section = "") {
  const revision = ++geoRevision;
  geography = null;
  options(local, [], "Selecione um município");
  options(secao, [], "Selecione um município");
  geoHint.textContent = "Escolha até o nível que deseja consultar. Pare na UF para ver o estado inteiro.";
  if (!municipio.value) {
    geoTask = Promise.resolve();
    return geoTask;
  }
  const state = uf.value;
  const city = municipio.value;
  geoHint.textContent = "Carregando locais e seções…";
  geoTask = detailed(year, state, city).then((data) => {
    if (revision !== geoRevision) return;
    geography = data;
    const keys = new Set();
    for (const [key, rows] of Object.entries(data?.s || {})) {
      const zone = key.split(":")[0];
      for (const row of rows) if (row?.[0] > 0) keys.add(`${zone}:${row[0]}`);
    }
    options(local, [...keys].map((key) => [key, locationLabel(data, key)]).sort(sortLabels),
      "Todos os locais", location);
    updateSections(section);
    geoHint.textContent = data
      ? "Os locais e seções listados têm registro de apuração em 2026. Você também pode escolher uma seção diretamente."
      : "A base de 2026 não tem registro por seção para este município.";
  }).catch(() => {
    if (revision !== geoRevision) return;
    geoHint.textContent = "Falha ao carregar locais e seções. Selecione o município novamente ou recarregue a página.";
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

function urlFor(sel) {
  const link = new URL(location.href);
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

function periods(sel) {
  if (sel.mode === "analisar") return [[year, +sel.turno]];
  if (sel.comparacao === "turnos") return [[year, 2], [year, 1]];
  const turn = sel.comparacao === "historico1" ? 1 : 2;
  return [[year, turn], [+sel.ano, turn]];
}

const periodLabel = ([ano, turno]) => `${ano} · ${turno}º turno`;

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
    name:"Outras categorias da apuração", votes:other,
    rates:other.map((value, i) => rate(value, results[i]?.values[1]))
  });
  return rows;
}

function table(name, rows, labels, type) {
  const comparing = labels.length === 2;
  const head = `<tr><th scope="col">${type}</th>${labels.map((label) =>
    `<th scope="col">${label}<br>Quantidade</th><th scope="col">${label}<br>Taxa</th>`).join("")}
    ${comparing ? '<th scope="col">Diferença</th><th scope="col">Diferença em p.p.</th>' : ""}</tr>`;
  return `<section class="panel table-panel"><h3>${name}</h3><div class="table-wrap" tabindex="0" role="region" aria-label="${name}"><table><thead>${head}</thead><tbody>${rows.map(({name, votes, rates}) =>
    `<tr><th scope="row">${html(name)}</th>${labels.map((_, i) => `<td>${n(votes[i])}</td><td>${pct(rates[i])}</td>`).join("")}
    ${comparing ? `<td>${signed(delta(...votes))}</td><td>${signed(delta(...rates), true)}</td>` : ""}</tr>`
  ).join("")}</tbody></table></div></section>`;
}

function chart(rows, labels) {
  const top = rows.filter((row) => row.rates.some((value) => value > 0)).slice(0, 6);
  if (!top.length) return "";
  return `<section class="panel chart"><div class="chart-head"><h3>Participação nos votos válidos</h3>
    <div class="legend">${labels.map((label, i) => `<span><i class="${i ? "base" : "focus"}-key"></i>${label}</span>`).join("")}</div></div>
    ${top.map(({name, rates}) => `<div class="chart-row"><strong>${html(name)}</strong><div>${labels.map((label, i) =>
      `<div class="bar-line" aria-label="${label}, ${pct(rates[i])}"><span class="track" aria-hidden="true">
      <i class="${i ? "base" : "focus"}-bar" style="width:${Math.min(100, rates[i] || 0)}%"></i></span><span>${pct(rates[i])}</span></div>`
    ).join("")}</div></div>`).join("")}</section>`;
}

function cards(rows, labels) {
  const comparing = labels.length === 2;
  return `<div class="metrics">${[0, 1, 3].map((idx) => {
    const {name, votes, rates} = rows[idx];
    const change = idx === 1 ? signed(delta(...rates), true) : signed(delta(...votes));
    const reference = `${n(votes[1])} na referência · diferença ${change}`;
    return `<div class="panel metric"><span>${name}</span><b>${n(votes[0])}</b><small>${comparing ? reference : (idx ? pct(rates[0]) : labels[0])}</small></div>`;
  }).join("")}</div>`;
}

function territory(sel) {
  const city = catalog.uf[sel.uf]?.[sel.municipio];
  const trail = [sel.uf, city && titleCase(city)].filter(Boolean);
  if (sel.local && !sel.secao) trail.push("Local de votação");
  if (sel.secao) trail.push("Seção eleitoral");
  const name = sel.secao ? sectionLabel(sel.secao) : sel.local ? locationLabel(geography, sel.local) :
    city ? titleCase(city) : states[sel.uf];
  return {name, trail: trail.join(" / ")};
}

function show(sel, periodList, results) {
  const labels = periodList.map(periodLabel);
  const notes = [];
  results.forEach((result, i) => {
    if (!result) notes.push(`Sem registro para este recorte em ${labels[i]}.`);
    else if (!result.votes) notes.push(`Em ${labels[i]}, a soma nominal diverge do detalhe da apuração em pelo menos uma seção deste recorte. O painel exibe os totais de apuração e omite a distribuição por candidato para esse período.`);
  });
  if (results[0]?.sectionKeys && results[1]?.sectionKeys) {
    const [a, b] = results;
    if (a.loc !== b.loc) notes.push("A seção aparece em locais de votação diferentes nos dois períodos.");
    if (a.locationName && b.locationName && a.locationName !== b.locationName) {
      notes.push("O nome do local consta de forma diferente nos dois períodos. Confira a correspondência territorial antes de interpretar as diferenças.");
    }
    if (a.sectionKeys.length !== b.sectionKeys.length || a.sectionKeys.some((key) => !b.sectionKeys.includes(key))) {
      notes.push(`O local reúne conjuntos diferentes de seções: ${a.sectionKeys.length} no período em foco e ${b.sectionKeys.length} na referência.`);
    }
  }
  const candidates = candidateRows(periodList, results);
  const indicators = metricRows(results);
  const found = results.some(Boolean);
  const nominal = results.some((result) => result?.votes);
  const notices = notes.map((note) => `<p class="notice">${html(note)}</p>`).join("");
  $("output").innerHTML = notices + (found ?
    cards(indicators, labels) + (nominal ? chart(candidates, labels) + table("Votação nominal", candidates, labels, "Candidatura") : "") +
    table("Eleitorado e apuração", indicators, labels, "Indicador") +
    '<p class="hint">Taxas de candidatos sobre válidos. Comparecimento e abstenções sobre aptos. Válidos, brancos e nulos sobre comparecimento. O traço indica dado indisponível ou candidatura ausente no turno.</p>' : "");
  if (results[0]?.address) $("subtitle").textContent += " · " + titleCase(results[0].address);
  visibleReport = found ? {sel, labels, indicators, candidates: nominal ? candidates : []} : null;
  $("actions").hidden = !found;
  $("status").textContent = found ? "" : "Nenhum resultado disponível para a consulta.";
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
  $("subtitle").textContent = labels.length === 2 ? `Foco: ${labels[0]} · Referência: ${labels[1]}` : labels[0];
  $("status").textContent = "Carregando os resultados…";
  $("output").replaceChildren();
  $("actions").hidden = true;
  visibleReport = null;
  if (focus) $("resultado-titulo").focus();
  try {
    const results = await Promise.all(periodList.map((period) => loadResult(sel, period)));
    if (revision !== runRevision) return;
    show(sel, periodList, results);
    history.replaceState(null, "", urlFor(sel));
  } catch {
    if (revision === runRevision) $("status").textContent = "Falha ao carregar os resultados. Tente novamente.";
  }
}

function csv() {
  if (!visibleReport) return;
  const {sel, labels, indicators, candidates} = visibleReport;
  const compare = labels.length === 2;
  const context = [sel.uf, sel.municipio, sel.local, sel.secao];
  const header = ["UF", "Município TSE", "Local (zona:código)", "Seção (zona:número)", "Tipo", "Indicador",
    ...labels.flatMap((label) => [label + " quantidade", label + " taxa (%)"]),
    ...(compare ? ["Diferença", "Diferença (p.p.)"] : [])];
  const cell = (value) => '"' + String(value ?? "").replaceAll('"', '""') + '"';
  const num = (value) => value == null ? "" : value.toFixed(2).replace(".", ",");
  const rows = [header];
  for (const [kind, list] of [["Apuração", indicators], ["Candidato", candidates]]) {
    for (const {name, votes, rates} of list) rows.push([...context, kind, name,
      ...labels.flatMap((_, i) => [votes[i], num(rates[i])]),
      ...(compare ? [delta(...votes), num(delta(...rates))] : [])]);
  }
  const file = new Blob(["\uFEFF", rows.map((row) => row.map(cell).join(";")).join("\r\n")],
    {type:"text/csv;charset=utf-8"});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(file);
  link.download = `atlas-${context.filter(Boolean).join("-").replaceAll(":", "-")}.csv`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

async function start() {
  const params = new URLSearchParams(location.search);
  form.querySelector('button[type="submit"]').disabled = true;
  options(uf, [], "Carregando…");
  try {
    catalog = await fetchData("catalogo.json");
  } catch {
    $("status").textContent = "Não foi possível abrir o catálogo eleitoral. Recarregue a página para tentar novamente.";
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
  form.addEventListener("change", updateMode);
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
      $("status").textContent = "Link da consulta copiado.";
    } catch {
      window.prompt("Copie o link da consulta", link);
    }
  });
  form.querySelector('button[type="submit"]').disabled = false;
  run();
}

start();
