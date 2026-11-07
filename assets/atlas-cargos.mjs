export const offices = ["presidente", "governador", "senador"];

export function officeName(cargo, t) {
  return { presidente:t("Presidente", "President"), governador:t("Governador", "Governor"),
    senador:t("Senador", "Senator") }[cargo] || t("Presidente", "President");
}

export function officePeriods(sel) {
  if (sel.mode === "analisar") return [[2026, Number(sel.turno)]];
  if (sel.comparacao === "turnos") return [[2026, 2], [2026, 1]];
  const turn = sel.comparacao === "historico1" ? 1 : 2;
  return [[2026, turn], [Number(sel.ano), turn]];
}

const sum = (rows, field) => rows.every((row) => row[field] != null) ?
  rows.reduce((total, row) => total + row[field], 0) : null;
const ratio = (a, b) => a != null && b > 0 ? 100 * a / b : null;

export function createOfficeData(manifest, read) {
  function coverage(sel, [ano, turno]) {
    const info = manifest.ufs[sel.uf]?.[sel.cargo];
    if (ano !== 2026 || !info) return "fora_cobertura";
    if (!info.turnos.includes(turno)) return turno === 2 && info.segundo_turno === "nao_houve_disputa" ?
      "nao_houve_disputa" : "nao_publicado";
    if (sel.municipio && !info.municipios.includes(sel.municipio)) return "fora_cobertura";
    if ((sel.local || sel.secao) && !info.detalhados.includes(sel.municipio)) return "fora_cobertura";
    return "disponivel";
  }
  async function pack(sel) {
    const info = manifest.ufs[sel.uf]?.[sel.cargo];
    return info ? read(info.base + "/municipios.json") : null;
  }
  async function detailed(sel) {
    const info = manifest.ufs[sel.uf]?.[sel.cargo];
    if (!info?.detalhados.includes(sel.municipio)) return null;
    return read(info.base + "/secoes-" + sel.municipio + ".json.gz", true);
  }
  async function loadResult(sel, period) {
    if (coverage(sel, period) !== "disponivel") return null;
    const [, turno] = period;
    if (!sel.local && !sel.secao) {
      const data = await pack(sel);
      const row = data.registros[sel.municipio]?.[turno];
      return row ? { values:row.slice(0, 6), votes:Object.fromEntries(row.slice(6)),
        ...data.extras[sel.municipio][turno] } : null;
    }
    const data = await detailed(sel);
    const section = sel.secao && data.secoes[sel.secao];
    const entries = sel.secao ? section?.[turno] ? [[sel.secao,section]] : [] :
      Object.entries(data.secoes).filter(([, turns]) => turns[turno]?.local === sel.local);
    if (!entries.length) return null;
    const rows = entries.map(([, turns]) => turns[turno]);
    const values = Array.from({length:6}, (_, i) => rows.every((row) => row.values[i] != null) ?
      rows.reduce((total, row) => total + row.values[i], 0) : null);
    const votes = rows.every((row) => row.votes) ? {} : null;
    if (votes) for (const row of rows) for (const [key, value] of Object.entries(row.votes)) {
      votes[key] = (votes[key] || 0) + value;
    }
    const loc = rows[0].local;
    return { values, votes, totalVotes:sum(rows, "totalVotes"), ordinaryNull:sum(rows, "ordinaryNull"),
      technicalNull:sum(rows, "technicalNull"), annulled:sum(rows, "annulled"),
      subjudice:sum(rows, "subjudice"), sectionKeys:entries.map(([key]) => key), loc,
      locationName:data.locais[loc]?.[0], address:data.locais[loc]?.[1] };
  }
  return { coverage, pack, detailed, loadResult };
}

export function officeMetricRows(results, t) {
  const specs = [
    ["0",t("Aptos", "Eligible voters"), (r) => r.values[0], () => null],
    ["1",t("Comparecimento", "Turnout"), (r) => r.values[1], (r) => r.values[0]],
    ["2",t("Abstenção", "Abstention"), (r) => r.values[2], (r) => r.values[0]],
    ["3",t("Votos válidos", "Valid votes"), (r) => r.values[3], (r) => r.totalVotes],
    ["4",t("Brancos", "Blank votes"), (r) => r.values[4], (r) => r.totalVotes],
    ["5",t("Nulos", "Invalid votes"), (r) => r.values[5], (r) => r.totalVotes],
    ["total",t("Total de votos do cargo", "Total votes for the office"), (r) => r.totalVotes, () => null]
  ];
  const rows = specs.map(([key,name,count,denominator]) => ({
    key:"m:" + key, name, votes:results.map((r) => r ? count(r) : null),
    rates:results.map((r) => r ? ratio(count(r), denominator(r)) : null)
  }));
  for (const [field,label,en] of [
    ["ordinaryNull","Nulos comuns","Ordinary invalid votes"],
    ["technicalNull","Nulos técnicos","Technical invalid votes"],
    ["annulled","Anulados","Annulled votes"],
    ["subjudice","Anulados sub judice","Votes annulled pending judgment"]
  ]) {
    if (results.some((r) => r?.[field] > 0)) rows.push({
      key:"m:" + field, name:t(label,en),
      votes:results.map((r) => r?.[field] ?? null),
      rates:results.map((r) => ratio(r?.[field], r?.totalVotes))
    });
  }
  return rows;
}

export function officeCandidateRows(pack, periodList, results) {
  const people = new Map();
  periodList.forEach(([ano, turn], i) => {
    if (ano !== 2026) return;
    for (const [code, candidate] of Object.entries(pack?.candidatos[turn] || {})) {
      const key = candidate.id;
      if (!people.has(key)) people.set(key, {
        key:"c:" + key, name:candidate.nome + " (" + candidate.partido + ")",
        fullName:candidate.nomeCompleto, votes:periodList.map(() => null), rates:periodList.map(() => null)
      });
      if (results[i]?.votes) {
        const row = people.get(key);
        row.votes[i] = results[i].votes[code] || 0;
        row.rates[i] = ratio(row.votes[i], results[i].values[3]);
      }
    }
  });
  return [...people.values()].sort((a,b) => (b.votes[0] ?? -1) - (a.votes[0] ?? -1) ||
    a.name.localeCompare(b.name, "pt-BR"));
}

export function coverageNote(status, cargo, ano, turno, t) {
  if (status === "disponivel") return "";
  const name = officeName(cargo,t);
  if (status === "nao_houve_disputa") return t(
    `Não houve disputa de ${name} no ${turno}º turno de ${ano} nesta UF.`,
    `There was no ${name} election in round ${turno} of ${ano} in this state.`);
  return t(`Dados de ${name} para ${ano}, ${turno}º turno, ainda não estão na cobertura deste recorte.`,
    `${name} data for ${ano}, round ${turno}, are not yet covered for this selection.`);
}

export function officeRateNote(cargo, t) {
  const base = t("Candidatos sobre votos válidos do cargo. Comparecimento e abstenção sobre aptos. Válidos, brancos e nulos sobre o total de votos do cargo.",
    "Candidate shares use valid votes for the office. Turnout and abstention use eligible voters. Valid, blank and invalid vote shares use total votes for the office.");
  return cargo === "senador" ? base + " " + t(
    "Em 2026, cada eleitor tem duas escolhas para senador. Nulos comuns e técnicos detalham o total de nulos.",
    "In 2026, each voter has two Senate choices. Ordinary and technical invalid votes are components of total invalid votes.") : base;
}
