import { createOfficeData, officePeriods, officeMetricRows, officeCandidateRows,
  officeName, coverageNote, officeRateNote } from "../../assets/atlas-cargos.mjs";

const normalize = value => String(value || "").normalize("NFD").replace(/\p{Diacritic}/gu,"").toUpperCase();
const diff = (a,b) => a == null || b == null ? null : a-b;

export async function chatOffice(query, context, env, locale, {territory, dataReader}) {
  const t = (pt,en) => /^en(?:-|$)/i.test(locale) ? en : pt;
  const cargo = query.cargo || context.cargo;
  const name = officeName(cargo,t);
  const atlas = new URL(env.ATLAS_URL);
  const reader = dataReader(atlas);
  const [catalog, manifest] = await Promise.all([
    reader.published("catalogo.json"), reader.published("cargos-2026.json")
  ]);
  const data = createOfficeData(manifest, reader.published);
  const sel = territory(query, context, catalog);
  const clarify = message => ({type:"clarification", message});
  if (typeof sel === "string") return clarify(sel);
  sel.cargo = cargo;
  const availableTurns = manifest.ufs[sel.uf]?.[cargo]?.turnos || [];
  const activeTurn = context.cargo === cargo ? Number(context.turno) : availableTurns.at(-1);
  sel.turno = String(query.turno ?? (cargo === "senador" ? 1 : activeTurn || 1));
  sel.comparacao = query.anoReferencia === 2026 || query.intencao === "comparacao" ? "turnos" : "";
  sel.mode = query.intencao === "comparacao" ? "comparar" : "analisar";
  sel.ano = "";
  const urlFor = selection => {
    const url = new URL(/^en(?:-|$)/i.test(locale) ? "en/" : "./",atlas);
    for (const key of ["cargo","uf","municipio","local","secao","mode","turno","comparacao"]) {
      if (selection[key]) url.searchParams.set(key,selection[key]);
    }
    url.hash = "explorador";
    return url.href;
  };
  async function suggestion(selection, label) {
    const results = await Promise.all(officePeriods(selection).map(period => data.loadResult(selection,period)));
    return results.every(Boolean) ? {label,explorerUrl:urlFor(selection)} : null;
  }
  async function guidance(message, selection = sel) {
    const single = {...selection,mode:"analisar",turno:"1",comparacao:"",ano:""};
    const suggestions = [
      await suggestion(single,t(`Consultar ${name} no 1º turno de 2026`,`View ${name} in 2026 round 1`))
    ];
    if ((selection.local || selection.secao) && !suggestions[0]) {
      suggestions.push(await suggestion({...single,local:"",secao:""},
        t("Consultar o município no 1º turno de 2026","View the municipality in 2026 round 1")));
    } else if (cargo === "governador") {
      suggestions.push(await suggestion({...selection,mode:"comparar",comparacao:"turnos",ano:""},
        t("Comparar os turnos de 2026","Compare the 2026 rounds")));
    }
    return {message,suggestions:suggestions.filter(Boolean)};
  }
  if (!["consulta","comparacao","causa"].includes(query.intencao)) {
    return {type:"unsupported", message:t(
      "Posso consultar resultados de Presidente, Governador e Senador.",
      "I can look up President, Governor and Senator results."),
      guidance:await guidance(t("Veja a cobertura disponível para este cargo.","See the available coverage for this office."))};
  }
  if ([query.ano,query.anoReferencia].some(value => value != null && value !== 2026)) {
    return {type:"unsupported",message:t(
      "O histórico deste cargo ainda está em preparação. A cobertura atual é de 2026.",
      "Historical results for this office are in preparation. Current coverage is for 2026."),
      guidance:await guidance(t("Posso consultar os resultados de 2026.","I can look up 2026 results."))};
  }
  if (query.intencao === "comparacao" && cargo === "senador") {
    return {type:"unsupported",message:t("Senador é disputado em turno único.","Senator elections have a single round."),
      guidance:await guidance(t("Posso mostrar os candidatos, brancos e nulos de 2026.",
        "I can show candidates and blank and invalid votes for 2026."))};
  }
  if (query.nivel === "local" || query.nivel === "secao" || query.local || query.secao || sel.local || sel.secao) {
    const detail = await data.detailed(sel);
    if (!detail) return {type:"unsupported",message:t(
      "Os dados deste local ou seção ainda estão fora da cobertura para o cargo.",
      "This polling place or section is not yet covered for this office."),
      guidance:await guidance(t("Você pode consultar a cobertura municipal.","You can check municipal coverage."))};
    const keys = Object.keys(detail.secoes);
    if (query.nivel === "secao" || query.secao) {
      if (!query.secao) return clarify(t("Qual é o número da seção e da zona eleitoral?",
        "What are the polling section and electoral zone numbers?"));
      const matches = keys.filter(key => Number(key.split(":")[1]) === query.secao &&
        (!query.zona || Number(key.split(":")[0]) === query.zona));
      if (matches.length !== 1) return clarify(t(
        "Confira o número da seção e informe a zona eleitoral.","Check the section number and provide the electoral zone."));
      sel.secao = matches[0];
      sel.local = "";
    } else if (query.nivel === "local" || query.local) {
      if (!query.local) return clarify(t("Qual é o nome ou o código do local de votação?",
        "What is the polling place name or code?"));
      const matches = Object.keys(detail.locais).filter(key =>
        (!query.zona || Number(key.split(":")[0]) === query.zona) &&
        (key === query.local || Number(key.split(":")[1]) === Number(query.local) ||
          normalize(detail.locais[key][0]) === normalize(query.local)));
      if (matches.length !== 1) return clarify(t(
        "Confira o nome do local ou informe seu código e a zona.","Check the place name or provide its code and electoral zone."));
      sel.local = matches[0];
      sel.secao = "";
    }
  }
  if (query.intencao === "causa") {
    return {type:"unsupported",message:t(
      "Os resultados permitem medir diferenças, mas são insuficientes para determinar a causa.",
      "The results can measure differences but are insufficient to establish a cause."),
      guidance:await guidance(t("Estas consultas mostram os resultados disponíveis.",
        "These queries show the available results."))};
  }
  const periodList = officePeriods(sel);
  const results = await Promise.all(periodList.map(period => data.loadResult(sel,period)));
  const coverage = periodList.map((period,i) => ({ano:period[0],turno:period[1],available:!!results[i],
    status:data.coverage(sel,period),sections:results[i]?.sectionKeys?.length ?? null}));
  const notes = coverage.flatMap(({ano,turno,status},i) => [
    ...(!results[i] ? [coverageNote(status,cargo,ano,turno,t)] : []),
    ...(results[i] && !results[i].votes ? [t(
      "A votação nominal e a destinação dos votos ainda não foram conciliadas para este recorte.",
      "Candidate votes and their allocation have not been reconciled for this selection.")] : [])
  ]);
  notes.push(officeRateNote(cargo,t));
  const found = results.some(Boolean);
  const pack = found ? await data.pack(sel) : null;
  const indicators = officeMetricRows(results,t);
  const candidates = officeCandidateRows(pack,periodList,results);
  const match = normalize(query.candidato);
  const named = match ? candidates.filter(row => normalize(row.fullName).includes(match) || normalize(row.name).includes(match)) : [];
  if (match && named.length !== 1) notes.push(t(
    "O nome solicitado não identifica uma candidatura única. Confira os nomes disponíveis.",
    "The requested name does not identify a single candidate. Check the available names."));
  const metric = query.indicador && query.indicador !== "candidatos";
  const rows = metric ? indicators.filter(row => row.key === "m:" + query.indicador) :
    [...indicators,...(named.length === 1 ? named : candidates)];
  const table = rows.map(row => ({
    key:row.key,name:row.name,counts:row.votes,rates:row.rates,
    ...(periodList.length === 2 && {
      countDelta:diff(...row.votes),rateDelta:row.key.startsWith("c:") ? diff(...row.rates) :
        row.rates[1] > 0 && row.rates[0] != null ? 100*(row.rates[0]-row.rates[1])/row.rates[1] : null,
      rateDeltaUnit:row.key.startsWith("c:") ? "pp" : "%"
    })
  }));
  const place = sel.municipio ? catalog.uf[sel.uf][sel.municipio] + " · " + sel.uf : sel.uf;
  return {type:found?"result":"no_data", message:t(`Resultado para ${name} em ${place}.`,`Results for ${name} in ${place}.`),
    filters:sel,periods:coverage,table:found?table:[],notes,explorerUrl:urlFor(sel),
    sources:reader.sources(), dataVersion:manifest.versao,
    ...(!results.every(Boolean) && {guidance:await guidance(t(
      "Você pode consultar estes resultados disponíveis.","You can view these available results."))})};
}
