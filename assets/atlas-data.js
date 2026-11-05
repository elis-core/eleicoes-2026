export const year = 2026;
export const states = {AC:"Acre", AL:"Alagoas", AP:"Amapá", AM:"Amazonas", BA:"Bahia", CE:"Ceará",
  DF:"Distrito Federal", ES:"Espírito Santo", GO:"Goiás", MA:"Maranhão", MT:"Mato Grosso",
  MS:"Mato Grosso do Sul", MG:"Minas Gerais", PA:"Pará", PB:"Paraíba", PR:"Paraná",
  PE:"Pernambuco", PI:"Piauí", RJ:"Rio de Janeiro", RN:"Rio Grande do Norte",
  RS:"Rio Grande do Sul", RO:"Rondônia", RR:"Roraima", SC:"Santa Catarina",
  SP:"São Paulo", SE:"Sergipe", TO:"Tocantins"};
export const titleCase = (s) => s.toLocaleLowerCase("pt-BR").replace(
  /(^|[^\p{L}])([\p{L}]+)/gu, (match, prefix, word, offset) =>
    prefix + (offset && ["de","do","da","das","dos","e"].includes(word) ? word : word[0].toUpperCase() + word.slice(1))
);
export const rate = (a, b) => b > 0 && a != null ? 100 * a / b : null;
export const delta = (a, b) => a == null || b == null ? null : a - b;
export const relativeChange = (focus, reference) => reference > 0 && focus != null ?
  100 * (focus - reference) / reference : null;
const ordered = new Intl.Collator("pt-BR", {numeric:true, sensitivity:"base"});

/** @returns {[number, number][] } */
export function periods(sel) {
  if (sel.mode === "analisar") return [[year, +sel.turno]];
  if (sel.comparacao === "turnos") return [[year, 2], [year, 1]];
  const turn = sel.comparacao === "historico1" ? 1 : 2;
  return [[year, turn], [+sel.ano, turn]];
}

export function localKeys(key, records) {
  const zone = key.split(":")[0];
  return records.filter(([section, turns]) =>
    section.split(":")[0] === zone && turns.some((row) => row && `${zone}:${row[0]}` === key)
  );
}

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

export function municipalResult(pack, city, turn) {
  const row = pack[city]?.[turn];
  return row ? {values: row.slice(0, 6), votes: Object.fromEntries(row.slice(6))} : null;
}

export function candidateRows(catalog, periodList, results) {
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

export function metricRows(results, t) {
  const metrics = [
    [t("Aptos", "Eligible voters"), 0, null], [t("Comparecimento", "Turnout"), 1, 0], [t("Abstenção", "Abstention"), 2, 0],
    [t("Votos válidos", "Valid votes"), 3, 1], [t("Brancos", "Blank votes"), 4, 1], [t("Nulos", "Invalid votes"), 5, 1]
  ];
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

/**
 * @param {object} catalog
 * @param {(path: string, compressed?: boolean) => Promise<any>} fetchData
 * @param {(url: string) => Promise<any>} fetchR2
 * @param {(url: string) => void} [useR2]
 */
export function createAtlasData(catalog, fetchData, fetchR2, useR2) {
  const rjMunicipalPacks = new Map();

  async function detailed(ano, state, city) {
    const pack = catalog.indice[ano]?.[state]?.[city];
    if (pack == null) return null;
    return (await fetchData(`secoes-${ano}-${state}-${pack}.json.gz`, true))[city] || null;
  }

  function loadRjMunicipalPack(ano) {
    if (!rjMunicipalPacks.has(ano)) {
      const path = `${ano}/presidente/RJ/municipios.json`;
      const pending = (async () => {
        try {
          const {release} = await fetchData("r2-rj-release.json");
          if (/^[a-f0-9]{40}-[0-9]+-[0-9]+$/.test(release)) {
            const url = "https://atlas-data.electoralintegrity.org/releases/" + release + "/" + path;
            const data = await fetchR2(url);
            const records = data.registros;
            if (data.schema === 1 && data.ano === ano && data.cargo === "presidente" &&
                data.uf === "RJ" && records?.[""] && Object.keys(records).length === 93 &&
                Object.values(records).every(turns =>
                  Array.isArray(turns?.[1]) && Array.isArray(turns?.[2]))) {
              useR2?.(url);
              return records;
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

  return {detailed, loadMunicipalPack, loadResult};
}
