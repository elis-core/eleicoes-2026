import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { createHash } from "node:crypto";
import { gunzipSync } from "node:zlib";
import { createOfficeData, officeMetricRows, officeCandidateRows } from "../assets/atlas-cargos.mjs";

const root = resolve(process.argv[2] || new URL("../dados/",import.meta.url).pathname);
const cache = new Map();
async function read(path, compressed=false) {
  const key = path + (compressed?".b64":"");
  if (!cache.has(key)) {
    const bytes = await readFile(join(root,key));
    const actual = compressed ? gunzipSync(Buffer.from(bytes.toString(),"base64")) : bytes;
    cache.set(key,JSON.parse(actual));
  }
  return cache.get(key);
}
const manifest = await read("cargos-2026.json");
for (const [file,hash] of Object.entries(manifest.arquivos)) {
  const bytes = await readFile(join(root,file));
  assert.equal(createHash("sha256").update(bytes).digest("hex"),hash,file);
}
const data = createOfficeData(manifest,read);
const t = value => value;
let checked = 0;
for (const [uf,cargos] of Object.entries(manifest.ufs)) for (const [cargo,info] of Object.entries(cargos)) {
  const sel = {uf,cargo,municipio:"",local:"",secao:"",mode:"analisar",turno:"1"};
  const pack = await data.pack(sel);
  for (const turn of info.turnos) {
    const expected = await data.loadResult(sel,[2026,turn]);
    const cities = await Promise.all(info.municipios.map(municipio =>
      data.loadResult({...sel,municipio},[2026,turn])));
    assert.deepEqual(expected.values,Array.from({length:6},(_,i) => cities.reduce((v,row) => v+row.values[i],0)));
    for (const field of ["totalVotes","ordinaryNull","technicalNull","annulled","subjudice"]) {
      assert.equal(expected[field],cities.reduce((v,row) => v+row[field],0),uf + " " + cargo + " " + field);
    }
    for (const municipio of info.municipios) {
      const citySel = {...sel,municipio};
      const municipal = await data.loadResult(citySel,[2026,turn]);
      const detail = await data.detailed(citySel);
      const sections = Object.keys(detail.secoes).filter(key => detail.secoes[key][turn]);
      const rows = await Promise.all(sections.map(secao => data.loadResult({...citySel,secao},[2026,turn])));
      assert(rows.length > 0);
      assert.deepEqual(municipal.values,Array.from({length:6},(_,i) => rows.reduce((v,row) => v+row.values[i],0)));
      assert.equal(municipal.totalVotes,rows.reduce((v,row) => v+row.totalVotes,0));
      const metrics = officeMetricRows([municipal],t);
      const blank = metrics.find(row => row.key === "m:4");
      assert.equal(blank.rates[0],100 * municipal.values[4]/municipal.totalVotes);
      const nominal = officeCandidateRows(pack,[[2026,turn]],[municipal]);
      assert.equal(nominal.reduce((v,row) => v+row.votes[0],0),municipal.values[3]);
      checked += rows.length;
    }
  }
}
const senateRJ = await data.loadResult({cargo:"senador",uf:"RJ",municipio:""},[2026,1]);
assert.equal(senateRJ.totalVotes,2*senateRJ.values[1]);
assert.equal(data.coverage({cargo:"governador",uf:"AP",municipio:"06050"},[2026,2]),"nao_houve_disputa");
assert.equal(await data.loadResult({cargo:"senador",uf:"RJ",municipio:""},[2026,2]),null);
assert.equal(await data.loadResult({cargo:"governador",uf:"SP",municipio:""},[2026,1]),null);
assert.equal(await data.loadResult({cargo:"governador",uf:"RN",municipio:""},[2022,1]),null);
console.log("Hashes, totais municipais e " + checked + " seção–turnos conciliados. Taxas do Senado e lacunas validadas.");
