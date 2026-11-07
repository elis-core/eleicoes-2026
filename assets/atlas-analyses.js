"use strict";

const atlasAnalyses = (() => {
  const root = new URL("../",document.currentScript.src);
  const en = document.documentElement.lang.startsWith("en");
  const normalize = value => String(value || "").normalize("NFD").replace(/\p{Diacritic}/gu,"")
    .toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
  const contains = (text,value) => (" " + text + " ").includes(" " + normalize(value) + " ");
  const studies = [
    {uf:"AP",municipio:"06050",ano:2026,cargos:["presidente"],nome:"Macapá",arquivos:{html:{url:new URL(
      (en?"en/":"") + "municipios/macapa/",root).href}}},
    {uf:"RJ",municipio:"58190",ano:2026,cargos:["presidente"],nome:"Campos dos Goytacazes",arquivos:{html:{url:new URL(
      (en?"en/":"") + "municipios/campos-dos-goytacazes/",root).href}}}
  ];
  let published = [];
  function safeUrl(value) {
    try {
      const url = new URL(value,root);
      const sameSite = url.origin === root.origin && /\/(?:en\/)?(?:municipios|analises)\//.test(url.pathname);
      const r2 = url.origin === "https://atlas-data.electoralintegrity.org" && url.pathname.startsWith("/analises/");
      return (url.protocol === "https:" || url.origin === root.origin) && (sameSite || r2) &&
        !url.username && !url.password ? url.href : null;
    } catch { return null; }
  }
  const ready = fetch(new URL("analises/catalogo.json",root),{cache:"no-cache"})
    .then(response => {
      if (response.status === 404) return null;
      if (!response.ok) throw new Error("Analysis catalogue unavailable");
      return response.json();
    }).then(catalog => {
      if (!catalog) return;
      if (catalog.schema !== 1 || !Array.isArray(catalog.analises)) throw new Error("Invalid analysis catalogue");
      published = catalog.analises.filter(item => typeof item.nome === "string" &&
        /^\d{5}$/.test(item.municipio) && /^[A-Z]{2}$/.test(item.uf) &&
        Array.isArray(item.cargos) && safeUrl(item.arquivos?.html?.url))
        .sort((a,b) => String(b.data || "").localeCompare(String(a.data || "")) ||
          String(b.versao || "").localeCompare(String(a.versao || ""),undefined,{numeric:true}));
    }).catch(() => {});
  function resolve(question, context, catalogue) {
    const text = normalize(question);
    if (!/\b(?:analise|estudo|relatorio|analysis|study|report)\b/.test(text)) return null;
    const state = Object.entries(catalogue.states).find(([code,name]) =>
      new RegExp("\\b"+code+"\\b").test(question) || contains(text,"uf "+code) ||
      contains(text,"estado de "+name) || contains(text,"estado do "+name) ||
      (normalize(name) === "para" ? /\bpará\b/i.test(question) : contains(text,name)))?.[0];
    const matches = Object.entries(catalogue.cities).flatMap(([uf,cities]) =>
      Object.entries(cities).filter(([,name]) => contains(text,name)).map(([municipio,name]) =>
        ({uf,municipio,name:normalize(name)})));
    matches.sort((a,b) => b.name.length-a.name.length);
    const best = matches.filter(item => item.name === matches[0]?.name && (!state || item.uf === state));
    const explicit = best.length === 1 ? best[0] : best.find(item => item.uf === context.uf);
    if (best.length && !explicit) return null;
    const filters = {...context,uf:explicit?.uf || state || context.uf,
      municipio:explicit?.municipio || (!state || state===context.uf ? context.municipio : "")};
    filters.cargo = /\b(?:governador|governor)\b/.test(text) ? "governador" :
      /\b(?:senador|senator|senate)\b/.test(text) ? "senador" :
      /\b(?:presidente|president)\b/.test(text) ? "presidente" : context.cargo || "presidente";
    const years = text.match(/\b20\d{2}\b/g) || [];
    const year = Number(years.at(-1) || 2026);
    const found = [...published,...studies].find(item => item.uf === filters.uf &&
      item.municipio === filters.municipio && item.ano === year && item.cargos.includes(filters.cargo));
    return {filters,entry:found && {title:found.nome,url:safeUrl(found.arquivos.html.url)},
      automatic:/\b(?:abr[aei]|abrir|open)\b/.test(text)};
  }
  return {ready,resolve};
})();
