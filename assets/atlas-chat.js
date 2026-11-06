"use strict";

(() => {
  const chat = document.getElementById("atlas-chat");
  if (!chat) return;

  const productionApi = {
    origin:"https://dark-term-1a8d.elis-electoral-integrity-strategies.workers.dev",
    enabled:true,
    reports:false
  };
  const localDevelopment = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);
  const localApi = localDevelopment && new URLSearchParams(location.search).get("atlas-chat-api") === "local";
  const demo = localDevelopment && !localApi;
  const enabled = localDevelopment || productionApi.enabled;
  const reportsEnabled = localDevelopment || productionApi.reports;
  const apiOrigin = localApi ? location.origin : productionApi.origin;
  const tr = (pt, en) => document.documentElement.lang.startsWith("en") ? en : pt;
  const get = id => document.getElementById(id);
  const form = get("atlas-chat-form");
  const input = get("atlas-chat-input");
  const send = get("atlas-chat-send");
  const status = get("atlas-chat-status");
  const log = get("atlas-chat-log");
  const history = [];
  const demoReceipts = new Set();
  let previousFilters, previousMetric, pendingQuestion, pendingNeed, explorerContext, activeReport, busy = false;

  const idle = demo ? tr("Modo de desenvolvimento. Dados do Explorador. Relatos simulados.",
    "Development mode. Explorer data. Simulated reports.") : enabled ?
    tr("Resultados presidenciais · Da UF à seção eleitoral", "Presidential results · From states to polling sections") :
    tr("Chat em preparação. O Explorador já está disponível abaixo.",
      "Chat integration in progress. The Explorer is available below.");
  status.textContent = idle;

  function element(tag, text, className) {
    const item = document.createElement(tag);
    if (text != null) item.textContent = text;
    if (className) item.className = className;
    return item;
  }

  function message(who, text) {
    const item = element("article", null, "atlas-chat-message atlas-chat-message--" + who);
    item.setAttribute("aria-label", who === "user" ? tr("Sua mensagem", "Your message") : "Atlas");
    if (text) item.append(element("p", text));
    log.hidden = false;
    log.append(item);
    requestAnimationFrame(() => {
      log.scrollTop += item.getBoundingClientRect().top - log.getBoundingClientRect().top;
    });
    return item;
  }

  function link(label, url) {
    const anchor = element("a", label);
    anchor.href = url;
    return anchor;
  }

  function makeButton(label, type = "button") {
    const button = element("button", label);
    button.type = type;
    return button;
  }

  async function post(path, data) {
    const response = await fetch(new URL(path, apiOrigin), {
      method:"POST", headers:{"Content-Type":"application/json"}, credentials:"omit",
      cache:"no-store", body:JSON.stringify(data), signal:AbortSignal.timeout(30000)
    });
    if (path === "/api/chat" && [400, 429].includes(response.status)) return response.json();
    if (!response.ok) throw new Error("Atlas API HTTP " + response.status);
    return response.json();
  }

  const normalize = text => text.normalize("NFD").replace(/\p{Diacritic}/gu, "")
    .toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const has = (text, name) => (" " + text + " ").includes(" " + name + " ");
  const clarify = (pt, en, need) => ({kind:"clarification", message:tr(pt,en), need});
  const unsupported = (pt, en) => ({kind:"unsupported", message:tr(pt,en)});

  function demoChat(question, context) {
    const text = normalize(question);
    if (!/\buf [a-z]{2}\b/.test(text) && /\b(?:no brasil|em todo o brasil|nationwide|across brazil|national total)\b/.test(text)) {
      return clarify("Qual UF você quer consultar? O Explorador exibe resultados por UF e recortes menores.",
        "Which state would you like to check? The Explorer shows state and local results.", "uf");
    }
    const base = previousFilters || context;
    const {states, cities, years} = atlasChatExplorer.catalogue;
    const stateHint = Object.entries(states).find(([code, name]) => has(text, "uf " + code.toLowerCase()) ||
      has(text, "estado de " + normalize(name)) || has(text, "estado do " + normalize(name)) ||
      has(text, "state of " + normalize(name)))?.[0] ||
      question.match(/\b(?:UF|em|no|na|in)\s+([A-Z]{2})\b/u)?.[1] ||
      (/^[A-Z]{2}$/.test(question) ? question : "");
    const found = Object.entries(cities).filter(([state]) => !stateHint || stateHint === state)
      .flatMap(([state, names]) => Object.entries(names)
        .map(([code, name]) => ({state, code, name:normalize(name)}))
        .filter(city => has(text, city.name))).sort((a, b) => b.name.length - a.name.length);
    const best = found.filter(city => city.name === found[0]?.name);
    const city = best.find(item => item.state === stateHint) || (best.length === 1 ? best[0] : null);
    if (best.length > 1 && !city) return clarify("Em qual UF fica o município?", "Which state is the municipality in?", "uf");
    const state = city?.state || stateHint || Object.entries(states)
      .find(([,name]) => has(text, normalize(name)))?.[0];
    const selectsState = Boolean(state && !city);
    const filters = {...base, visao:""};
    const explicitCity = city?.code || "";
    const keepsDetail = explicitCity === base.municipio && state === base.uf &&
      /\b(?:secao|section|local de votacao|polling place)\b/.test(text);
    if (city || selectsState) Object.assign(filters, {uf:state, municipio:explicitCity,
      local:keepsDetail ? base.local : "", secao:keepsDetail ? base.secao : ""});

    const section = text.match(/\b(?:secao|section) (?:eleitoral |polling )?(\d+)\b/);
    const place = text.match(/\b(?:local|polling place)(?: de votacao)? (?:codigo )?(\d+)\b/);
    const zone = text.match(/\b(?:zona|zone) (?:eleitoral )?(\d+)\b/);
    const asksSection = /\b(?:secao|section)\b/.test(text);
    const asksPlace = /\b(?:local de votacao|polling place|local [0-9]+)\b/.test(text);
    if (asksSection || asksPlace) {
      if (!filters.municipio) return clarify("Qual é o município?", "Which municipality?");
      const code = asksSection ? section : place;
      const field = asksSection ? "secao" : "local";
      if (code) {
        if (!zone) return clarify("Qual é o número da zona eleitoral?", "What is the electoral zone number?", "zona");
        filters[field] = String(+zone[1]) + ":" + String(+code[1]);
        filters[asksSection ? "local" : "secao"] = "";
      } else if (!filters[field]) {
        return asksSection ?
          clarify("Qual é o número da seção e da zona eleitoral?", "What are the polling section and zone numbers?", "secao") :
          clarify("Qual é o código do local e o número da zona? Você também pode selecioná-los no Explorador.", "What are the polling place code and zone number? You can also select them in the Explorer.", "local");
      }
    }
    if (!filters.uf || !Object.hasOwn(states, filters.uf)) return clarify("Qual é a UF da consulta?", "Which state should I look up?", "uf");
    if (/\b(?:governador|senador|deputad[oa]|governor|senate|senator|deputy)\b/.test(text)) {
      return unsupported("O chat consulta resultados para Presidente. Os resultados de outros cargos estão na seção Alianças, conforme a cobertura.",
        "The chat covers presidential results. Results for other offices are in the Alliances section where available.");
    }

    const first = /\b(?:1 o? ?turno|primeiro turno|first round)\b/.test(text);
    const second = /\b(?:2 o? ?turno|segundo turno|second round)\b/.test(text);
    const yearsAsked = [...new Set(text.match(/\b(?:19|20)\d{2}\b/g) || [])];
    if (yearsAsked.some(year => !Object.hasOwn(years, year))) {
      return unsupported("Esse ano está fora da cobertura do Explorador. Use 2010, 2014, 2018, 2022 ou 2026.",
        "That year is outside the Explorer coverage. Use 2010, 2014, 2018, 2022 or 2026.");
    }
    const comparison = /\b(?:compare|comparar|comparacao|comparison|versus|vs)\b/.test(text) ||
      (yearsAsked.length === 2 && yearsAsked.includes("2026"));
    const historical = yearsAsked.find(year => year !== "2026");
    if (historical && !comparison && !first && !second && !previousFilters) {
      return clarify("No Explorador, os anos anteriores entram em comparação com 2026. Qual turno você quer comparar?",
        "The Explorer compares earlier years with 2026. Which round would you like to compare?", "turno");
    }
    if (yearsAsked.filter(year => year !== "2026").length > 1 || (historical && first && second)) {
      return unsupported("Compare o mesmo turno de um pleito anterior com 2026 ou compare os dois turnos de 2026.",
        "Compare the same round of an earlier election with 2026, or compare the two rounds of 2026.");
    }
    if (comparison || historical || (first && second)) {
      let compare = "turnos";
      if (historical) {
        const usesFirst = first || (!second && (filters.comparacao === "historico1" || filters.turno === "1"));
        compare = usesFirst ? "historico1" : "historico2";
      } else if (!first && !second && filters.mode === "comparar" && !yearsAsked.length) {
        compare = filters.comparacao;
      }
      Object.assign(filters, {mode:"comparar", comparacao:compare, ano:historical || filters.ano});
    } else if (first || second) Object.assign(filters, {mode:"analisar", turno:first ? "1" : "2"});

    const indicators = [/\b(?:aptos|eligible voters|eleitorado)\b/, /\b(?:comparecimento|turnout)\b/,
      /\b(?:abstencao|abstention)\b/, /\b(?:validos|valid votes)\b/, /\b(?:brancos|blank votes)\b/,
      /\b(?:nulos|invalid votes)\b/];
    const idx = indicators.findIndex(pattern => pattern.test(text));
    const names = Object.values(years).flatMap(data => Object.values(data.candidatos));
    const candidate = names.find(([short, full]) => has(text, normalize(full)) || has(text, normalize(short)));
    const metric = idx >= 0 ? "m:" + idx : candidate ? "c:" + candidate[1].normalize("NFD")
      .replace(/\p{Diacritic}/gu, "").trim().replace(/\s+/g, " ").toUpperCase() : comparison ? "" : previousMetric || "";
    if (!state && !comparison && !first && !second && !historical && !candidate && idx < 0 && !asksSection &&
        !asksPlace && !/\b(?:resultado|resultados|results|votos|votes|votacao|presidente|president|consulta)\b/.test(text)) {
      return clarify("Posso consultar resultados presidenciais. Qual território ou indicador você quer consultar?",
        "I can look up presidential results. Which area or indicator would you like to check?");
    }
    return {kind:"result", selection:filters, metric};
  }

  function showResult(result) {
    if (!result.rows.length && !result.link) {
      const recorte = tr("Não há dados disponíveis para esse recorte na cobertura do Atlas.",
        "Data for that selection are unavailable in the Atlas coverage.");
      const indicador = tr("O indicador ou candidato solicitado não tem valores disponíveis nesse recorte.",
        "The requested indicator or candidate has no available values for that selection.");
      message("atlas", result.gaps.length ? recorte : indicador);
      return;
    }
    const reply = message("atlas");
    reply.append(element("h3", result.area));
    const comparing = result.labels.length === 2;
    const wrap = element("div", null, "table-wrap");
    wrap.tabIndex = 0;
    wrap.setAttribute("role", "region");
    wrap.setAttribute("aria-label", tr("Resultados da consulta", "Query results"));
    const table = element("table");
    const header = table.createTHead().insertRow();
    const headers = [tr("Indicador ou candidato", "Indicator or candidate"), ...result.labels];
    if (comparing) headers.push(tr("Diferença", "Change"));
    for (const label of headers) {
      const cell = element("th", label);
      cell.scope = "col";
      header.append(cell);
    }
    const body = table.createTBody();
    for (const row of result.rows) {
      const line = body.insertRow();
      const name = element("th", row.name);
      name.scope = "row";
      line.append(name);
      const values = comparing ? [...row.values, row.difference] : row.values;
      for (const [count, rate] of values) line.insertCell().textContent = rate === "—" ? count : count + " (" + rate + ")";
    }
    wrap.append(table);
    if (result.rows.length) reply.append(wrap);
    for (const note of result.notes ?? []) reply.append(element("p", note));
    if (result.gaps.length) reply.append(element("p", tr("Sem dados para ", "No data for ") + result.gaps.join(", ") + "."));
    if (result.candidateGap) reply.append(element("p", tr("A votação nominal está indisponível em pelo menos um período.",
      "Candidate vote totals are unavailable for at least one period.")));
    if (comparing) reply.append(element("p", tr("Diferenças do período em foco em relação à referência. As taxas dos candidatos variam em pontos percentuais e as de apuração em termos relativos.",
      "Changes compare the focus period with the reference. Candidate share changes are in percentage points and vote-count rate changes are relative.")));
    const sources = element("p");
    sources.append(link(tr("Abrir no Explorador", "Open in the Explorer"), result.link),
      link(tr("Fonte TSE e manifesto de ingestão", "TSE source and ingestion manifest"), result.source));
    reply.append(sources);
    if (result.versions.length) reply.append(element("p", tr("Versão dos dados no R2 ", "R2 data version ") +
      result.versions.map(([version, years]) => version + " (" + years.join(", ") + ")").join(", "), "atlas-chat-version"));
  }

  function showReceipt(reply, receipt, response) {
    const published = response.status === "published";
    if (published && (!Number.isSafeInteger(response.issueNumber) || response.issueNumber <= 0)) {
      throw new Error("Missing issue number");
    }
    reply.replaceChildren(element("p", tr("Comprovante privado ", "Private receipt ") + receipt));
    if (published) {
      reply.append(element("p", tr("Protocolo #", "Reference #") + response.issueNumber + "."),
        link(tr("Abrir Issue publicada", "Open published issue"),
          "https://github.com/elis-core/eleicoes-2026/issues/" + response.issueNumber));
    } else {
      const statusText = element("p", demo ? tr("Envio simulado. Nenhum relato foi encaminhado.", "Simulated submission. No report was sent.") :
        tr("Recebido para triagem privada. A Issue estará disponível aqui após a publicação.",
          "Received for private triage. The issue will appear here after publication."));
      reply.append(statusText);
      const check = makeButton(tr("Consultar situação", "Check status"));
      check.addEventListener("click", () => checkReceipt(reply, receipt, check, statusText));
      reply.append(check);
    }
  }

  async function checkReceipt(reply, receipt, button, note) {
    button.disabled = true;
    try {
      const response = demo ? {status:demoReceipts.has(receipt) ? "received" : "unknown"} :
        await post("/api/questoes", {action:"status", receipt});
      if (!["received", "triage", "published"].includes(response.status)) throw new Error("Unknown receipt");
      showReceipt(reply, receipt, response);
      const next = reply.querySelector("button, a");
      next?.focus({preventScroll:true});
      return true;
    } catch {
      note.textContent = tr("Não foi possível consultar esse comprovante. Confira o código ou tente novamente.", "Could not check that receipt. Check the code or try again.");
      button.disabled = false;
      return false;
    }
  }

  function openReport(summary = "") {
    if (!reportsEnabled) {
      message("atlas", tr("O envio privado de relatos ainda está em preparação.",
        "Private reporting is still in preparation."));
      return false;
    }
    if (activeReport) {
      activeReport.querySelector("textarea").focus();
      return false;
    }
    const reply = message("atlas");
    activeReport = reply;
    reply.append(element("h3", tr("Revise o resumo da questão", "Review the question summary")));
    reply.append(element("p", tr("O resumo segue para triagem privada após sua confirmação. Evite incluir dados pessoais desnecessários.",
      "The summary is sent for private triage after you confirm. Leave out unnecessary personal data.")));
    const draft = element("form", null, "atlas-chat-report");
    const label = element("label", tr("Resumo para triagem", "Summary for triage"));
    const field = element("textarea");
    field.required = true;
    field.maxLength = 2000;
    field.value = summary;
    label.append(field);
    const actions = element("div", null, "atlas-chat-report-actions");
    const submit = makeButton(tr("Confirmar envio privado", "Confirm private submission"), "submit");
    const cancel = makeButton(tr("Cancelar", "Cancel"));
    const note = element("p");
    note.setAttribute("role", "status");
    actions.append(submit, cancel);
    draft.append(label, actions, note);
    reply.append(draft);

    const lookup = element("form", null, "atlas-chat-report");
    const lookupLabel = element("label", tr("Já tem um comprovante? Cole o código.", "Already have a receipt? Paste the code."));
    const code = element("input");
    code.required = true;
    code.maxLength = 512;
    const lookupActions = element("div", null, "atlas-chat-report-actions");
    const lookupButton = makeButton(tr("Consultar situação", "Check status"), "submit");
    const lookupNote = element("p");
    lookupNote.setAttribute("role", "status");
    lookupLabel.append(code);
    lookupActions.append(lookupButton);
    lookup.append(lookupLabel, lookupActions, lookupNote);
    lookup.addEventListener("submit", async event => {
      event.preventDefault();
      if (!code.value.trim() || lookupButton.disabled) return;
      for (const control of [submit, cancel, field, code]) control.disabled = true;
      if (await checkReceipt(reply, code.value.trim(), lookupButton, lookupNote)) activeReport = null;
      else for (const control of [submit, cancel, field, code]) control.disabled = false;
    });
    reply.append(lookup);
    cancel.addEventListener("click", () => {
      reply.remove();
      activeReport = null;
      log.hidden = !log.childElementCount;
      input.focus({preventScroll:true});
    });

    let requestId, lastSummary;
    draft.addEventListener("submit", async event => {
      event.preventDefault();
      const reviewed = field.value.trim();
      if (!reviewed || submit.disabled) return;
      if (reviewed !== lastSummary) requestId = crypto.randomUUID();
      lastSummary = reviewed;
      for (const control of [submit, cancel, field, lookupButton, code]) control.disabled = true;
      note.textContent = tr("Enviando…", "Sending…");
      try {
        const receipt = "DEV-" + requestId;
        const response = demo ? {status:"received", receipt} :
          await post("/api/questoes", {action:"submit", summary:reviewed, requestId, locale:document.documentElement.lang});
        if (typeof response.receipt !== "string" || !response.receipt.trim() ||
            response.receipt.length > 512 || !["received", "triage", "published"].includes(response.status)) {
          throw new Error("Missing receipt");
        }
        if (demo) demoReceipts.add(receipt);
        showReceipt(reply, response.receipt, response);
        activeReport = null;
        reply.querySelector("button, a")?.focus({preventScroll:true});
      } catch {
        note.textContent = tr("O envio não foi confirmado. O resumo continua aqui para você tentar novamente.",
          "Submission was not confirmed. Your summary is still here so you can retry.");
        for (const control of [submit, cancel, field, lookupButton, code]) control.disabled = false;
      }
    });
    field.focus();
    return true;
  }

  async function ask(text) {
    const question = text.trim();
    if (!question || busy || !enabled) return;
    const reportIntent = normalize(question).match(/^(?:(?:quero|gostaria de|i want to|i would like to) )?(?:registrar (?:uma )?questao|relatar|enviar (?:um )?relato|raise (?:a )?question|submit (?:a )?report)\b(.*)$/);
    if (reportIntent) {
      const summary = question.includes(":") ? question.slice(question.indexOf(":") + 1).trim() :
        reportIntent[1].trim() ? question : "";
      if (openReport(summary)) input.value = "";
      return;
    }
    busy = true;
    send.disabled = true;
    input.value = "";
    message("user", question);
    status.textContent = tr("Consultando o Atlas…", "Checking the Atlas…");
    try {
      const explorer = await atlasChatExplorer.context();
      const currentContext = JSON.stringify(explorer);
      if (explorerContext && explorerContext !== currentContext) {
        previousFilters = previousMetric = pendingQuestion = pendingNeed = undefined;
        history.length = 0;
      }
      explorerContext = currentContext;
      const extra = pendingNeed === "uf" && /^[a-z]{2}$/i.test(question) ? "UF " + question.toUpperCase() :
        ["zona", "turno", "local", "secao"].includes(pendingNeed) && /^\d/.test(question) ?
          (pendingNeed === "turno" ? question + " turno" : pendingNeed + " " + question) : question;
      const answer = demo ? demoChat(pendingQuestion ? pendingQuestion + " " + extra : question, explorer) :
        await post("/api/chat", {message:question, locale:document.documentElement.lang,
          filters:previousFilters || explorer, history});
      if (answer.kind === "result") {
        const result = await atlasChatExplorer.result(answer.selection, answer.metric);
        showResult(result);
        if (result.selection) previousFilters = result.selection;
        previousMetric = answer.metric;
        pendingQuestion = pendingNeed = null;
      } else if (["result", "no_data"].includes(answer.type)) {
        showResult(atlasChatExplorer.workerResult(answer));
        previousFilters = answer.filters;
        pendingQuestion = pendingNeed = null;
      } else if (["clarification", "unsupported", "report", "error"].includes(answer.type) &&
        typeof answer.message === "string") {
        message("atlas", answer.message);
        if (answer.type === "error") {
          if (!input.value) input.value = question;
          return;
        }
      } else if (["clarification", "unsupported"].includes(answer.kind) && typeof answer.message === "string") {
        message("atlas", answer.message);
        pendingNeed = answer.need;
        pendingQuestion = answer.kind === "clarification" ? [pendingQuestion, question].filter(Boolean).join(" ").slice(-2000) : null;
      } else {
        throw new Error("Unknown Atlas chat reply");
      }
      history.push(question);
      if (history.length > 5) history.shift();
    } catch {
      message("atlas", tr("Não foi possível conectar ao Atlas. Sua pergunta está no campo para tentar novamente.",
        "Could not connect to the Atlas. Your question is in the composer so you can try again."));
      if (!input.value) input.value = question;
    } finally {
      busy = false;
      send.disabled = false;
      status.textContent = idle;
    }
  }

  form.addEventListener("submit", event => { event.preventDefault(); ask(input.value); });
  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing && enabled) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  chat.querySelectorAll("[data-chat-prompt]").forEach(button => {
    button.disabled = !enabled;
    button.addEventListener("click", () => {
      if (busy) return;
      input.value = button.querySelector("span").textContent;
      input.focus();
      form.requestSubmit();
    });
  });
  const reportButton = chat.querySelector("[data-chat-report]");
  reportButton.disabled = !enabled || !reportsEnabled;
  if (!reportsEnabled) reportButton.querySelector("span").textContent =
    tr("Envio privado em preparação.", "Private reporting in preparation.");
  reportButton.addEventListener("click", () => openReport());
  send.disabled = !enabled;

  const desktop = matchMedia("(min-width: 701px) and (hover: hover) and (pointer: fine)").matches;
  if (enabled && desktop && !location.hash && !new URLSearchParams(location.search).has("uf")) {
    input.focus({preventScroll:true});
  }
})();
