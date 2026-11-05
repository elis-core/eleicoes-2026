import {
  candidateRows, createAtlasData, delta, metricRows, periods, relativeChange, states, titleCase, year
} from "../../assets/atlas-data.js";
import {interpret, type Query} from "./interpret.ts";

interface Env {
  ATLAS_URL: string;
  ALLOWED_ORIGINS: string;
  OPENAI_MODEL: string;
  OPENAI_API_KEY?: string;
  CHAT_LIMIT: {limit(input: {key: string}): Promise<{success: boolean}>};
}

type Catalog = {
  uf: Record<string, Record<string, string>>;
  indice: Record<string, Record<string, Record<string, number>>>;
};
type Input = Record<string, unknown>;
type PeriodResult = {
  votes?: Record<string, number> | null;
  sectionKeys?: string[];
  loc?: string;
  locationName?: string;
} | null;
type Filters = {
  uf: string; municipio: string; local: string; secao: string;
  mode: "analisar" | "comparar"; turno: string; comparacao: string; ano: string;
};

const service = "elis-atlas-customer-service";
const historicalYears = [2010, 2014, 2018, 2022];
const maxBody = 8192;
const text = (value: unknown) => typeof value === "string" ? value.trim() : "";
const record = (value: unknown): value is Input => !!value && typeof value === "object" && !Array.isArray(value);
const normalized = (value: string) => value.normalize("NFD").replace(/\p{Diacritic}/gu, "")
  .replace(/[^\p{L}\p{N}]+/gu, " ").trim().toUpperCase();
const keyPattern = /^\d{1,6}:\d{1,6}$/;

class ClientError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function requestBody(request: Request) {
  if (request.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase() !== "application/json") {
    throw new ClientError(415, "Envie um objeto JSON.");
  }
  const reader = request.body?.getReader();
  if (!reader) throw new ClientError(400, "Envie um objeto JSON.");
  const decoder = new TextDecoder();
  let size = 0, body = "";
  for (;;) {
    const {value, done} = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > maxBody) {
      await reader.cancel();
      throw new ClientError(413, "A mensagem é muito longa.");
    }
    body += decoder.decode(value, {stream: true});
  }
  try {
    const parsed: unknown = JSON.parse(body + decoder.decode());
    if (record(parsed)) return parsed;
  } catch {
    // Mensagens inválidas recebem o mesmo erro de contrato.
  }
  throw new ClientError(400, "Envie um objeto JSON válido.");
}

function dataReader(atlas: URL) {
  const sources = new Map<string, {url: string; sha256: string}>();
  const published = new Map<string, Promise<unknown>>();
  const selectedR2 = new Set<string>();
  async function read(url: URL, compressed: boolean, timeout: number) {
    const response = await fetch(url, {signal: AbortSignal.timeout(timeout), redirect: "error"});
    if (!response.ok) throw new Error("Dados indisponíveis");
    const bytes = await response.arrayBuffer();
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    const sha256 = Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
    const decoded = compressed ? await new Response(new Blob([Uint8Array.from(
      atob(new TextDecoder().decode(bytes)), (character) => character.charCodeAt(0)
    )]).stream().pipeThrough(new DecompressionStream("gzip"))).json() : JSON.parse(new TextDecoder().decode(bytes));
    sources.set(url.href, {url: url.href, sha256});
    return decoded;
  }
  return {
    published(path: string, compressed = false) {
      const url = new URL("dados/" + path + (compressed ? ".b64" : ""), atlas);
      if (!published.has(url.href)) published.set(url.href, read(url, compressed, 6500));
      return published.get(url.href)!;
    },
    r2: (url: string) => read(new URL(url), false, 3500),
    useR2: (url: string) => selectedR2.add(url),
    sources: () => [...sources.values()].filter(({url}) => published.has(url) || selectedR2.has(url))
  };
}

function territory(query: Query, filters: Input, catalog: Catalog): Filters | string {
  const requestedState = text(query.uf);
  const stateName = normalized(requestedState);
  const explicit = requestedState && Object.keys(catalog.uf).find((uf) =>
    uf === stateName || normalized(states[uf as keyof typeof states]) === stateName);
  if (requestedState && !explicit) return "Qual é a sigla da UF?";

  const name = normalized(text(query.municipio));
  const activeState = text(filters.uf);
  let uf = explicit || activeState;
  let municipio = "";
  if (name) {
    const matches = Object.entries(catalog.uf).flatMap(([state, cities]) => explicit && state !== explicit ? [] :
      Object.entries(cities).filter(([code, label]) => code === name || normalized(label) === name)
        .map(([code]) => [state, code]));
    if (matches.length > 1) return "Há municípios com esse nome em mais de uma UF. Qual é a UF?";
    if (!matches.length) return "Não encontrei esse município no catálogo do Atlas. Qual é o nome e a UF?";
    [uf, municipio] = matches[0];
  } else if (query.nivel !== "uf" && uf === activeState) {
    municipio = text(filters.municipio);
  }
  if (!Object.hasOwn(catalog.uf, uf)) return "Qual UF ou município você quer consultar?";
  if (municipio && !Object.hasOwn(catalog.uf[uf], municipio)) return "Qual é o município?";
  if (query.nivel === "municipio" && !municipio) return "Qual é o município?";

  const sameCity = municipio && uf === activeState && municipio === text(filters.municipio);
  const hasDetail = query.nivel === "local" || query.nivel === "secao" || !!(query.local || query.secao);
  const inheritDetail = !hasDetail && !query.nivel && !requestedState && !name && sameCity;
  const local = inheritDetail ? text(filters.local) : "";
  const secao = inheritDetail ? text(filters.secao) : "";
  if (hasDetail && !municipio) return "Qual é o município e a UF desse local ou seção?";
  return {
    uf, municipio, local: keyPattern.test(local) ? local : "", secao: keyPattern.test(secao) ? secao : "",
    mode: query.intencao === "comparacao" ? "comparar" : "analisar", turno: "2", comparacao: "", ano: ""
  };
}

function setPeriods(query: Query, context: Input, sel: Filters): string | undefined {
  const activeTurn = Number(text(context.turno));
  const first = query.ano ?? year;
  const second = query.anoReferencia ?? (context.mode === "comparar" && context.comparacao !== "turnos" ?
    Number(text(context.ano)) || undefined : undefined);
  if (sel.mode === "analisar") {
    if (first !== year) return "A consulta de um único turno no Explorador está disponível para 2026. Posso comparar com 2010, 2014, 2018 ou 2022.";
    const turn = query.turno ?? activeTurn;
    if (turn !== 1 && turn !== 2) return "Você quer consultar o 1º ou o 2º turno de 2026?";
    sel.turno = String(turn);
    return;
  }
  if (first === year && (second === year ||
      (second == null && query.turno != null && query.turnoReferencia != null && query.turno !== query.turnoReferencia) ||
      (second == null && context.mode === "comparar" && context.comparacao === "turnos"))) {
    if (query.turno != null && query.turno === query.turnoReferencia) return "Quais períodos você quer comparar?";
    sel.comparacao = "turnos";
    return;
  }
  const reference = first === year ? second : first;
  if (reference == null) return "Você quer comparar os turnos de 2026 ou comparar 2026 com outro ano?";
  if (!historicalYears.includes(reference) || (first !== year && second != null && second !== year)) {
    return "Qual ano você quer comparar com 2026? O Atlas tem 2010, 2014, 2018 e 2022.";
  }
  if (query.turno && query.turnoReferencia && query.turno !== query.turnoReferencia) {
    return "Na comparação histórica, escolha o mesmo turno nos dois anos. Quer o 1º ou o 2º turno?";
  }
  const inherited = context.mode === "comparar" && context.comparacao === "historico1" ? 1 :
    context.mode === "comparar" && context.comparacao === "historico2" ? 2 : activeTurn;
  const turn = query.turno ?? query.turnoReferencia ?? inherited;
  if (turn !== 1 && turn !== 2) return "Quer comparar o 1º ou o 2º turno dos dois anos?";
  sel.comparacao = "historico" + turn;
  sel.ano = String(reference);
}

function resolveDetail(query: Query, sel: Filters, pack: {s: Record<string, unknown[][]>; l: Record<string, string[]>} | null) {
  const isSection = query.nivel === "secao" || !!query.secao;
  const isLocal = query.nivel === "local" || !!query.local;
  if (!isSection && !isLocal && !sel.local && !sel.secao) return;
  if (!pack) return "O Atlas não tem registros por seção para esse município em 2026.";

  const entries = Object.entries(pack.s);
  const locals = new Set<string>();
  for (const [key, turns] of entries) {
    for (const row of turns) {
      if (Number(row?.[0]) > 0) locals.add(key.split(":")[0] + ":" + row[0]);
    }
  }
  if (isSection) {
    if (!query.secao) return "Qual é o número da seção e da zona eleitoral?";
    const matches = entries.map(([key]) => key).filter((key) => {
      const [zone, section] = key.split(":").map(Number);
      return section === query.secao && (!query.zona || zone === query.zona);
    });
    if (matches.length !== 1) return matches.length ? "Qual é a zona eleitoral dessa seção?" :
      "Não encontrei essa seção em 2026. Confira a zona e o número da seção.";
    sel.secao = matches[0];
    sel.local = "";
  } else if (isLocal) {
    const local = text(query.local);
    if (!local) return "Qual é o nome ou o código do local de votação?";
    const matches = [...locals].filter((key) => {
      const [zone, code] = key.split(":").map(Number);
      return (!query.zona || zone === query.zona) && (key === local || code === Number(local) ||
        normalized(pack.l[key]?.[0] || "") === normalized(local));
    });
    if (matches.length !== 1) return matches.length ? "Qual é a zona eleitoral ou o código desse local?" :
      "Não encontrei esse local em 2026. Confira o nome ou informe o código e a zona.";
    sel.local = matches[0];
    sel.secao = "";
  } else if ((sel.secao && !Object.hasOwn(pack.s, sel.secao)) || (sel.local && !locals.has(sel.local))) {
    return "Qual é a zona e o número da seção ou o código do local de votação?";
  }
}

function explorerUrl(atlas: URL, sel: Filters) {
  const url = new URL(atlas);
  for (const key of ["uf", "municipio", "local", "secao", "mode"] as const) {
    if (sel[key]) url.searchParams.set(key, sel[key]);
  }
  if (sel.mode === "analisar") url.searchParams.set("turno", sel.turno);
  else {
    url.searchParams.set("comparacao", sel.comparacao);
    if (sel.ano) url.searchParams.set("ano", sel.ano);
  }
  url.hash = "explorador";
  return url.href;
}

const question = (message: string) => ({type: "clarification", message});

async function chat(message: string, history: string[], context: Input, env: Env) {
  const query = await interpret(message, history, context, env.OPENAI_API_KEY!, env.OPENAI_MODEL);
  if (query.intencao === "relato") {
    return {type: "report", message: "O recebimento privado de relatos será disponibilizado em uma próxima etapa."};
  }
  if (query.intencao === "fora_escopo") {
    return {type: "unsupported", message: "Nesta etapa, posso consultar e comparar resultados para Presidente disponíveis no Atlas."};
  }
  if (query.intencao === "esclarecer") return question("Qual resultado ou comparação eleitoral você quer consultar?");
  const atlas = new URL(env.ATLAS_URL);
  const reader = dataReader(atlas);
  const catalog = await reader.published("catalogo.json") as Catalog;
  const sel = territory(query, context, catalog);
  if (typeof sel === "string") return question(sel);
  const periodError = setPeriods(query, context, sel);
  if (periodError) return question(periodError);

  const data = createAtlasData(catalog, reader.published, reader.r2, reader.useR2);
  if (query.nivel === "local" || query.nivel === "secao" || query.local || query.secao || sel.local || sel.secao) {
    const pack = await data.detailed(year, sel.uf, sel.municipio);
    const detailError = resolveDetail(query, sel, pack);
    if (detailError) return question(detailError);
  }

  const periodList = periods(sel);
  const results: PeriodResult[] = await Promise.all(periodList.map((period) => data.loadResult(sel, period)));
  const notes: string[] = [];
  const coverage = periodList.map(([ano, turno]: number[], i: number) => {
    const result = results[i];
    const label = `${ano}, ${turno}º turno`;
    if (!result) notes.push(`Sem registro para este recorte em ${label}.`);
    else if (!result.votes) notes.push(`A distribuição por candidato está indisponível em ${label}. Os totais de apuração continuam disponíveis.`);
    return {ano, turno, available: !!result, sections: result?.sectionKeys?.length ?? null};
  });
  const [focus, reference] = results;
  if (focus?.sectionKeys && reference?.sectionKeys) {
    if (focus.loc !== reference.loc || (focus.locationName && reference.locationName && focus.locationName !== reference.locationName)) {
      notes.push("A identificação do local de votação mudou entre os períodos. Confira a correspondência territorial no Explorador.");
    }
    const referenceKeys = new Set(reference.sectionKeys);
    if (focus.sectionKeys.length !== referenceKeys.size || focus.sectionKeys.some((key: string) => !referenceKeys.has(key))) {
      notes.push("Os períodos abrangem conjuntos diferentes de seções eleitorais.");
    }
  }
  const indicators = metricRows(results, (pt: string) => pt);
  const candidates = results.some((result) => result?.votes) ? candidateRows(catalog, periodList, results) : [];
  const candidate = normalized(text(query.candidato));
  const named = candidate ? candidates.filter(({key, name}: {key: string; name: string}) => {
    return normalized(name).includes(candidate) || normalized(key.slice(2)).includes(candidate);
  }) : [];
  if (candidate && candidates.length && named.length !== 1) {
    notes.push(named.length ? "O nome informado corresponde a mais de um candidato." :
      "O candidato informado não foi localizado nos turnos consultados.");
  }
  const selected = query.indicador && query.indicador !== "candidatos"
    ? indicators.filter(({key}: {key: string}) => key === "m:" + query.indicador) : indicators;
  const table = [...selected, ...(query.indicador && query.indicador !== "candidatos" && !candidate ?
    [] : named.length === 1 ? named : candidates)].map(({key, name, votes, rates}) => ({
      key, name, counts: votes.slice(0, periodList.length), rates: rates.slice(0, periodList.length),
      ...(periodList.length === 2 && {
        countDelta: delta(votes[0], votes[1]),
        rateDelta: key.startsWith("c:") ? delta(rates[0], rates[1]) : relativeChange(rates[0], rates[1]),
        rateDeltaUnit: key.startsWith("c:") ? "pp" : "%"
      })
    }));
  const place = sel.municipio ? titleCase(catalog.uf[sel.uf][sel.municipio]) + " · " + sel.uf : states[sel.uf as keyof typeof states];
  const subdivision = sel.secao ? ` · seção ${sel.secao.split(":")[1]}, zona ${sel.secao.split(":")[0]}` :
    sel.local ? ` · local ${sel.local.split(":")[1]}, zona ${sel.local.split(":")[0]}` : "";
  const found = results.some(Boolean);
  return {
    type: found ? "result" : "no_data",
    message: found ? `Resultado para Presidente em ${place}${subdivision}.` : "Não há resultados para os recortes solicitados.",
    filters: sel, periods: coverage, table: found ? table : [], notes,
    explorerUrl: explorerUrl(atlas, sel), sources: reader.sources()
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const {pathname} = new URL(request.url);
    const origin = request.headers.get("Origin");
    const allowed = !origin || env.ALLOWED_ORIGINS.split(",").map((entry) => entry.trim()).includes(origin);
    const headers = new Headers({"Cache-Control": "no-store", "Vary": "Origin", "X-Content-Type-Options": "nosniff"});
    if (origin && allowed) headers.set("Access-Control-Allow-Origin", origin);
    const json = (payload: unknown, status = 200) => Response.json(payload, {status, headers});
    const error = (message: string, status: number) => json({type: "error", message}, status);
    if (pathname === "/api/health" && request.method === "GET") {
      return json({service, status: env.OPENAI_API_KEY && env.CHAT_LIMIT ? "ready" : "setup_required"});
    }
    if (pathname !== "/api/chat") return error("Rota indisponível.", 404);
    if (!allowed) return error("Origem indisponível.", 403);
    if (request.method === "OPTIONS") {
      headers.set("Access-Control-Allow-Methods", "POST, OPTIONS");
      headers.set("Access-Control-Allow-Headers", "Content-Type");
      return new Response(null, {status: 204, headers});
    }
    if (request.method !== "POST") {
      headers.set("Allow", "POST, OPTIONS");
      return error("Use POST.", 405);
    }
    if (!env.OPENAI_API_KEY || !env.CHAT_LIMIT) return error("O atendimento está em configuração.", 503);
    try {
      const body = await requestBody(request);
      const message = text(body.message);
      if (!message || message.length > 1200) return error("Digite uma pergunta de até 1.200 caracteres.", 400);
      const history = Array.isArray(body.history) ? body.history.slice(-4).map((entry) => text(entry).slice(0, 1200)).filter(Boolean) : [];
      const input = record(body.filters) ? body.filters : {};
      const context = Object.fromEntries(["uf", "municipio", "local", "secao", "turno", "mode", "comparacao", "ano"]
        .map((key) => [key, text(input[key]).slice(0, 64)]));
      const {success} = await env.CHAT_LIMIT.limit({key: request.headers.get("CF-Connecting-IP") || "unknown"});
      if (!success) {
        headers.set("Retry-After", "60");
        return error("Limite de perguntas atingido. Tente novamente em um minuto.", 429);
      }
      return json(await chat(message, history, context, env));
    } catch (cause) {
      if (cause instanceof ClientError) return error(cause.message, cause.status);
      return error("O Atlas não conseguiu completar a consulta. Tente novamente.", 503);
    }
  }
};
