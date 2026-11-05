import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {test} from "node:test";
import worker from "./index.ts";

const atlas = "https://atlas-brazil-2026.electoralintegrity.org";
const env = {
  ATLAS_URL: atlas + "/",
  ALLOWED_ORIGINS: atlas,
  OPENAI_MODEL: "gpt-4.1-mini",
  OPENAI_API_KEY: "test",
  CHAT_LIMIT: {limit: async () => ({success: true})}
};
const data = (path) => readFile(new URL("../../dados/" + path, import.meta.url));
const jsonData = async (path) => JSON.parse(await data(path));
const query = (overrides) => ({
  intencao: "consulta", nivel: null, uf: null, municipio: null, local: null, zona: null, secao: null,
  ano: null, anoReferencia: null, turno: null, turnoReferencia: null, indicador: null, candidato: null,
  ...overrides
});

function mockSources(t, intent, {r2 = false} = {}) {
  let calls = 0;
  t.mock.method(globalThis, "fetch", async (input, init) => {
    const url = new URL(input);
    if (url.hostname === "api.openai.com") {
      calls++;
      const body = JSON.parse(init.body);
      assert.equal(body.store, false);
      assert.equal(body.text.format.strict, true);
      return Response.json({
        status: "completed",
        output: [{type: "message", content: [{type: "output_text", text: JSON.stringify(intent)}]}]
      });
    }
    if (url.hostname === "atlas-data.electoralintegrity.org") {
      if (!r2) return new Response(null, {status: 403});
      return new Response(await data(url.pathname.split("/").slice(3).join("/")));
    }
    assert.equal(url.origin, atlas);
    return new Response(await data(url.pathname.slice("/dados/".length)));
  });
  return () => calls;
}

function request(message = "Teste", filters = {}, origin = atlas) {
  return new Request(atlas + "/api/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json", Origin: origin},
    body: JSON.stringify({message, filters})
  });
}

test("reproduz os totais e as taxas de Campos em 2026 e 2022 com fallback do R2", async (t) => {
  const calls = mockSources(t, query({
    intencao: "comparacao", municipio: "Campos dos Goytacazes", ano: 2026, anoReferencia: 2022, turno: 2, indicador: "2"
  }));
  const response = await worker.fetch(request(), env);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Access-Control-Allow-Origin"), atlas);
  const result = await response.json();
  const catalog = await jsonData("catalogo.json");
  const code = Object.keys(catalog.uf.RJ).find((key) => catalog.uf.RJ[key] === "CAMPOS DOS GOYTACAZES");
  const rows = await Promise.all([2026, 2022].map(async (year) =>
    (await jsonData(year + "/presidente/RJ/municipios.json")).registros[code][2]));
  const [metric] = result.table;
  assert.equal(result.type, "result");
  assert.deepEqual(metric.counts, rows.map((row) => row[2]));
  assert.deepEqual(metric.rates, rows.map((row) => 100 * row[2] / row[0]));
  assert.equal(metric.countDelta, rows[0][2] - rows[1][2]);
  assert.equal(result.sources.filter(({url}) => url.includes("/presidente/")).length, 2);
  assert.ok(result.sources.every(({url, sha256}) => url.startsWith(atlas) && /^[a-f0-9]{64}$/.test(sha256)));
  const link = new URL(result.explorerUrl);
  assert.equal(link.searchParams.get("municipio"), code);
  assert.equal(link.searchParams.get("comparacao"), "historico2");
  assert.equal(link.searchParams.get("ano"), "2022");
  assert.equal(calls(), 1);
});

test("identifica a fonte R2 quando o pacote estadual é aceito", async (t) => {
  mockSources(t, query({nivel: "uf", uf: "RJ", turno: 2}), {r2: true});
  const response = await worker.fetch(request(), env);
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.type, "result");
  assert.ok(result.sources.some(({url}) => url.startsWith("https://atlas-data.electoralintegrity.org/releases/")));
});

test("reproduz uma seção de 2026 e sinaliza a ausência da mesma seção em 2010", async (t) => {
  const catalog = await jsonData("catalogo.json");
  const uf = "AP", city = "06050";
  const readSections = async (year) => {
    const index = catalog.indice[year][uf][city];
    const bytes = await data(`secoes-${year}-${uf}-${index}.json.gz.b64`);
    const decoded = new Blob([Buffer.from(bytes.toString(), "base64")]).stream().pipeThrough(new DecompressionStream("gzip"));
    return (await new Response(decoded).json())[city].s;
  };
  const [current, historical] = await Promise.all([readSections(2026), readSections(2010)]);
  const [key, rows] = Object.entries(current).find(([key, rows]) => rows[1] && !historical[key]?.[1]);
  const [zona, secao] = key.split(":").map(Number);
  mockSources(t, query({
    intencao: "comparacao", nivel: "secao", municipio: "Macapá", zona, secao, anoReferencia: 2010, turno: 2, indicador: "2"
  }));
  const result = await (await worker.fetch(request(), env)).json();
  assert.equal(result.type, "result");
  assert.deepEqual(result.periods.map(({available}) => available), [true, false]);
  assert.deepEqual(result.table[0].counts, [rows[1][3], null]);
  assert.equal(new URL(result.explorerUrl).searchParams.get("secao"), key);
});

test("pede esclarecimento sem inventar turno e bloqueia chamadas antes da OpenAI", async (t) => {
  const calls = mockSources(t, query({municipio: "Macapá", indicador: "2"}));
  const badOrigin = await worker.fetch(request("Teste", {}, "https://other.example"), env);
  assert.equal(badOrigin.status, 403);
  const limited = await worker.fetch(request(), {...env, CHAT_LIMIT: {limit: async () => ({success: false})}});
  assert.equal(limited.status, 429);
  assert.equal(calls(), 0);
  const result = await (await worker.fetch(request(), env)).json();
  assert.equal(result.type, "clarification");
  assert.match(result.message, /turno/);
});
