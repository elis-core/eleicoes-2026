const { copyFileSync, existsSync, readFileSync, renameSync, writeFileSync } = require("node:fs");
const { spawnSync } = require("node:child_process");
const { join, resolve } = require("node:path");

function update(source) {
  if (source.includes('import { chatOffice } from "./atlas-cargos-chat.mjs";')) return source;
  function replace(pattern, value, name) {
    const matches = source.match(new RegExp(pattern.source, pattern.flags.replace("g","") + "g"));
    if (matches?.length !== 1) throw new Error("Estrutura divergente em src/worker.js (" + name + ").");
    source = source.replace(pattern,value);
  }
  replace(/var properties = \{/, 'var properties = {\n  cargo: { type: ["string", "null"], enum: ["presidente", "governador", "senador", null] },', "esquema");
  replace(/Classifique o pedido de um visitante do Atlas Eleitoral do Brasil\./,
    `Classifique o pedido de um visitante do Atlas Eleitoral do Brasil.
O Atlas cobre Presidente, Governador e Senador. Extraia cargo sempre que expresso.
Governador e Senador têm consultas de 2026. Use consulta, comparacao ou causa para estes cargos.
Se o pedido comparar cargos distintos na mesma pergunta, use esclarecer para pedir a escolha de um cargo.
Senador é turno único com duas vagas em 2026. Se for solicitado um segundo turno, extraia turno 2 para explicar a ausência.
Presidente usa a cobertura histórica descrita a seguir. Para Governador e Senador, extraia também anos históricos solicitados para explicar o limite.
Em perguntas de seguimento, complete o cargo pelo histórico. Use null quando o cargo não for indicado.`, "instruções");
  replace(/Cargos diferentes,/, "Cargos de deputado federal, estadual ou distrital,", "escopo");
  replace(/  const query = await interpret\(message, history, context, [^;\r\n]+\);/,
    `$&
  const office = query.cargo || (["presidente", "governador", "senador"].includes(context.cargo) ? context.cargo : "presidente");
  if (office !== "presidente" && query.intencao !== "relato") {
    return chatOffice({ ...query, cargo: office }, context, env, locale, { territory, dataReader });
  }`, "roteamento");
  replace(/\["uf", "municipio", "local", "secao", "turno", "mode", "comparacao", "ano"\]\.map\(\(key\) => \[key, text\(input\[key\]\)\.slice\(0, 64\)\]\)/,
    '["cargo", "uf", "municipio", "local", "secao", "turno", "mode", "comparacao", "ano"].map((key) => [key, text(input[key]).slice(0, 64)])', "filtros");
  return 'import { chatOffice } from "./atlas-cargos-chat.mjs";\n' + source;
}
function main() {
  const root = resolve(process.argv[2] || ".");
  const path = join(root,"src","worker.js");
  const previous = readFileSync(path,"utf8");
  const next = update(previous.replace(/^\uFEFF/,""));
  const wrapper = readFileSync(join(root,"src","atlas-com-questoes.mjs"),"utf8");
  if (!wrapper.includes('./worker.js')) throw new Error("Entrada do Worker de relatos divergente.");
  const guidancePath = join(root,"src","atlas-chat-guidance.mjs");
  const guidance = readFileSync(guidancePath,"utf8");
  const nextGuidance = guidance
    .replace("O Atlas cobre resultados presidenciais. Escolha uma UF ou um município para consultar os dados disponíveis.",
      "O Atlas cobre Presidente, Governador e Senador. Escolha uma UF ou um município para verificar a cobertura.")
    .replace("The Atlas covers presidential results. Choose a state or municipality to see the available data.",
      "The Atlas covers President, Governor and Senator results. Choose a state or municipality to check coverage.")
    .replace("A pergunta vai além dos resultados presidenciais disponíveis no Atlas.",
      "A pergunta vai além da cobertura atual do Atlas.")
    .replace("This question goes beyond the presidential results available in the Atlas.",
      "This question goes beyond current Atlas coverage.");
  const modules = ["atlas-cargos-chat.mjs","atlas-cargos.mjs"];
  const shared = existsSync(join(__dirname,"atlas-cargos.mjs")) ? join(__dirname,"atlas-cargos.mjs") :
    resolve(__dirname,"../../assets/atlas-cargos.mjs");
  const contents = file => file === "atlas-cargos.mjs" ? readFileSync(shared,"utf8") :
    readFileSync(join(__dirname,file),"utf8").replace('from "../../assets/atlas-cargos.mjs"', 'from "./atlas-cargos.mjs"');
  for (const content of [next,nextGuidance,...modules.map(contents)]) {
    const check = spawnSync(process.execPath,["--input-type=module","--check"],{input:content,encoding:"utf8"});
    if (check.error || check.status !== 0) throw new Error(check.stderr || String(check.error));
  }
  for (const file of modules) {
    const target = join(root,"src",file);
    if (existsSync(target) && readFileSync(target,"utf8") !== contents(file)) {
      throw new Error("Já existe outra versão de " + target);
    }
  }
  if (previous !== next) {
    const backup = path + ".antes-dos-cargos";
    if (existsSync(backup) || existsSync(guidancePath + ".antes-dos-cargos")) {
      throw new Error("Já existe um backup antes dos cargos. Confira o arquivo antes de aplicar.");
    }
    copyFileSync(path,backup);
    copyFileSync(guidancePath,guidancePath + ".antes-dos-cargos");
    for (const file of modules) writeFileSync(join(root,"src",file),contents(file));
    writeFileSync(path + ".novo",next,{flag:"wx"});
    renameSync(path + ".novo",path);
    writeFileSync(guidancePath,nextGuidance);
  }
  console.log("Worker preparado para Governador e Senador. Valide com wrangler deploy --dry-run.");
}
if (require.main === module) {
  try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
}
