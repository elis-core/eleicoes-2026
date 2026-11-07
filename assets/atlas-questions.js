"use strict";

const atlasQuestions = (() => {
  const list = document.getElementById("atlas-question-list");
  const empty = document.getElementById("atlas-history-empty");
  const clear = document.getElementById("atlas-history-clear");
  const panel = document.getElementById("atlas-history-panel");
  const storage = document.getElementById("atlas-history-storage");
  const tr = (pt,en) => document.documentElement.lang.startsWith("en") ? en : pt;
  const key = "elis.atlas.questions.v1";
  const states = ["pending","result","clarification","unsupported","error","analysis","report"];
  const fields = ["cargo","uf","municipio","local","secao","mode","turno","comparacao","ano","visao"];
  let entries = [], active = "", restore = () => {};
  function filters(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
    return Object.fromEntries(fields.filter(field => typeof value[field] === "string")
      .map(field => [field,value[field].slice(0,64)]));
  }
  function clean(entry) {
    if (!entry || typeof entry.id !== "string" || typeof entry.question !== "string" ||
        !states.includes(entry.state) || !Number.isFinite(entry.date) || entry.date < 0 || entry.date > Date.now()+86400000) return null;
    return {
      id:entry.id.slice(0,80),question:entry.question.slice(0,1200),date:entry.date,state:entry.state,
      filters:filters(entry.filters),context:filters(entry.context),
      metric:typeof entry.metric === "string" ? entry.metric.slice(0,160) : "",
      message:typeof entry.message === "string" ? entry.message.slice(0,1600) : "",
      history:Array.isArray(entry.history) ? entry.history.filter(item => typeof item === "string")
        .slice(-4).map(item => item.slice(0,1200)) : []
    };
  }
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "[]");
    if (Array.isArray(saved)) entries = saved.map(clean).filter(Boolean).slice(0,50);
    for (const entry of entries) if (entry.state === "pending") entry.state = "error";
  } catch { storage.textContent = tr("Histórico disponível nesta sessão.","History is available for this session."); }
  function persist() {
    try { localStorage.setItem(key,JSON.stringify(entries)); }
    catch { storage.textContent = tr("Histórico disponível nesta sessão.","History is available for this session."); }
  }
  function render() {
    const focused = list.contains(document.activeElement) ? document.activeElement.dataset.questionId : null;
    list.replaceChildren();
    for (const entry of entries) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.questionId = entry.id;
      const title = document.createElement("span");
      title.textContent = entry.question;
      const detail = document.createElement("small");
      const status = {
        pending:tr("Consultando…","Checking…"),result:tr("Ver resultados","View results"),
        clarification:tr("Completar pergunta","Complete question"),unsupported:tr("Ver orientação","View guidance"),
        error:tr("Tentar novamente","Try again"),analysis:tr("Abrir análise","Open analysis"),
        report:tr("Registrar questão","Raise a question")
      }[entry.state];
      detail.textContent = status + " · " + new Intl.DateTimeFormat(document.documentElement.lang,
        {day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"}).format(entry.date);
      button.append(title,detail);
      if (entry.id === active) button.setAttribute("aria-current","true");
      button.addEventListener("click",() => restore({...entry}));
      item.append(button);
      list.append(item);
    }
    if (focused) [...list.querySelectorAll("button")].find(button => button.dataset.questionId === focused)?.focus({preventScroll:true});
    empty.hidden = entries.length > 0;
    clear.hidden = entries.length === 0;
  }
  clear.addEventListener("click",() => { entries = []; active = ""; persist(); render(); });
  if (matchMedia("(min-width: 1000px)").matches) panel.open = true;
  render();
  return {
    onRestore(callback) { restore = callback; },
    add(question, context, history) {
      const id = crypto.randomUUID?.() || Date.now().toString(36) + "-" + crypto.getRandomValues(new Uint32Array(2)).join("-");
      const entry = clean({id,question,date:Date.now(),state:"pending",context,history});
      entries.unshift(entry);
      entries = entries.slice(0,50);
      active = id;
      persist(); render();
      return id;
    },
    update(id, change) {
      const index = entries.findIndex(entry => entry.id === id);
      if (index < 0) return;
      entries[index] = clean({...entries[index],...change});
      persist(); render();
    },
    select(id) { active = id; render(); }
  };
})();
