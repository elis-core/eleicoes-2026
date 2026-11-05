"use strict";

(function alliancesRJ() {
  const box = $("aliancas-consulta");
  const status = $("aliancas-status");
  const target = $("aliancas-conteudo");
  const stateLabel = $("aliancas-uf");
  const officeNames = {
    governador: t("Governador", "Governor"), senador: t("Senado", "Senate")
  };
  const formalNames = {
    mesmo_partido: t("Mesmo partido do presidenciável", "Same party as presidential candidate"),
    federacao_coligada: t("Federação na coligação presidencial", "Federation in presidential coalition")
  };
  const municipalName = t("Município", "Municipality");
  const presidential = t("Presidente", "President");
  const candidate = t("Candidato", "Candidate");
  const stateCandidate = t("Candidato estadual", "State candidate");
  const gapLabel = t("Presidente menos estadual", "President minus state candidate");
  const registration = t("Registro estadual", "State registration");
  const countLabel = t("Votos válidos", "Valid votes");
  const shareLabel = t("% dos válidos", "% of valid votes");
  const formatDate = (value) => new Intl.DateTimeFormat(locale, {timeZone: "UTC"}).format(new Date(value));
  const nameWithParty = ({nome, partido}) => `${titleCase(nome)} (${partido})`;
  const mobileLabel = (label) => `<span class="alliance-cell-label" aria-hidden="true">${label}</span>`;
  let loading = false;
  let ready = false;
  let syncMunicipality;

  function dataLink(source) {
    return `<a href="${html(source.url)}">${html(source.nome)}</a> · <time datetime="${html(source.data)}">${formatDate(source.data)}</time>`;
  }

  function init(cities, presidentialPack, offices, alliances) {
    const area = Object.entries(cities).map(([code, name]) => [code, titleCase(name)]).sort(sortLabels);
    const cityNames = Object.fromEntries(area);
    const presidentOptions = Object.entries(alliances.presidencia).map(([code, info]) => [code, nameWithParty(info)]);
    target.innerHTML = `
      <p class="hint">${t("Comparação do desempenho de Flávio Bolsonaro e Lula com candidatos estaduais com vínculo partidário formal ou apoio público documentado.", "Compare Flávio Bolsonaro and Lula with state candidates linked by formal party affiliation or documented public endorsement.")}</p>
      <div class="fields alliance-controls">
        <label>${municipalName}<select id="alianca-municipio"></select></label>
        <label>${presidential}<select id="alianca-presidente"></select></label>
        <label>${stateCandidate}<select id="alianca-candidato"></select></label>
        <label>${t("Ordenar por", "Sort by")}<select id="alianca-ordem"></select></label>
      </div>
      <p id="alianca-orientacao" class="hint" role="status">${t("Selecione um município para consultar as alianças.", "Select a municipality to view alliances.")}</p>
      <div id="alianca-resultado" hidden>
      <h3 id="alianca-localidade"></h3>
      <div class="actions"><button id="alianca-csv" type="button">${t("Baixar comparação em CSV", "Download comparison CSV")}</button></div>
      <div class="table-wrap alliance-results" tabindex="0" role="region" aria-label="${t("Comparação de alianças", "Alliance comparison")}">
        <table class="alliance-table" role="table"><thead role="rowgroup"><tr role="row">
        <th scope="col" role="columnheader">${stateCandidate}</th><th scope="col" role="columnheader">${presidential}</th>
        <th scope="col" role="columnheader">${gapLabel}</th></tr></thead>
        <tbody id="alianca-linhas" role="rowgroup"></tbody></table>
      </div>
      <p class="hint">${t(
        "Cada percentual usa os votos válidos do próprio cargo no município. No Senado, o denominador soma os votos válidos para as duas vagas. As diferenças descrevem resultados agregados entre cargos.",
        "Each percentage uses valid votes for that office in the municipality. The Senate denominator totals valid votes for both seats. Differences describe aggregate results across offices."
      )}</p>
      <details><summary>${t("Fontes e classificação dos vínculos", "Sources and relationship classifications")}</summary>
        <p class="hint">${t(
          "Apoio público indica declaração do presidenciável. Vínculo formal indica mesmo partido ou participação da federação do candidato estadual na coligação presidencial. A coligação estadual é registrada separadamente.",
          "Public endorsement indicates a statement by the presidential candidate. A formal link indicates the same party or membership of the state candidate’s federation in the presidential coalition. State coalitions are recorded separately."
        )}</p><ul id="alianca-fontes"></ul>
      </details></div>
      <details class="alliance-official">
        <summary>${t("Resultados oficiais por cargo", "Official results by office")}</summary>
        <div class="fields alliance-controls">
          <label>${t("Cargo", "Office")}<select id="rj-cargo"></select></label>
          <label class="alliance-toggle"><input id="rj-total-estadual" type="checkbox">${t("Exibir total estadual", "Show statewide total")}</label>
        </div>
        <p id="rj-total-validos" class="hint"></p>
        <div class="table-wrap alliance-results" tabindex="0" role="region" aria-label="${t("Resultados oficiais de Governador e Senado", "Official Governor and Senate results")}">
          <table class="alliance-table" role="table"><thead role="rowgroup"><tr role="row"><th scope="col" role="columnheader">${candidate}</th>
          <th scope="col" role="columnheader">${registration}</th><th scope="col" role="columnheader">${countLabel}</th>
          <th scope="col" role="columnheader">${shareLabel}</th></tr></thead><tbody id="rj-candidatos" role="rowgroup"></tbody></table>
        </div>
        <p class="hint">${t(
          "Governador usa a retotalização de 10/10. Os percentuais são calculados sobre os totais de votos válidos dos arquivos do TSE.",
          "Governor results use the 10 October retotalisation. Percentages are calculated from the valid-vote totals in the TSE files."
        )} <a href="https://dadosabertos.tse.jus.br/dataset/resultados-2026">${t("Dados do TSE", "TSE data")}</a> ·
        <a href="https://www.tre-rj.jus.br/comunicacao/noticias/2026/Outubro/tre-rj-proclama-douglas-ruas-pl-governador-eleito">${t("Retotalização do TRE-RJ", "TRE-RJ retotalisation")}</a></p>
      </details>`;

    const presidentSelect = $("alianca-presidente");
    const allySelect = $("alianca-candidato");
    const citySelect = $("alianca-municipio");
    const sortSelect = $("alianca-ordem");
    const officeSelect = $("rj-cargo");
    const statewide = $("rj-total-estadual");
    const allyName = (link) => nameWithParty(offices[link.cargo].candidatos[link.candidato]);
    const linkTypes = (link) => [
      ...(link.apoio ? [t("Apoio público", "Public endorsement")] : []),
      ...(link.formal ? [formalNames[link.formal]] : [])
    ].join(" · ");
    const linksFor = () => alliances.vinculos.filter((link) => link.presidente === presidentSelect.value);
    const paired = (votes, percentage, valid) => `${countWithRate(n(votes), pct(percentage))}
      <small class="alliance-note">${n(valid)} ${t("válidos no cargo", "valid for this office")}</small>`;

    options(presidentSelect, presidentOptions, "", "22");
    options(citySelect, area, t("Selecione um município", "Select a municipality"), municipio.value);
    options(sortSelect, [
      ["office", t("Por cargo", "By office")],
      ["high", t("Maior vantagem presidencial (p.p.)", "Largest presidential lead (pp)")],
      ["low", t("Maior vantagem estadual (p.p.)", "Largest state-candidate lead (pp)")]
    ]);
    options(officeSelect, Object.entries(officeNames));

    function refreshAllies() {
      options(allySelect, linksFor().map((link) => [
        `${link.cargo}:${link.candidato}`, `${allyName(link)} · ${officeNames[link.cargo]}`
      ]), t("Todos os vínculos", "All relationships"));
    }

    function renderComparison() {
      const code = citySelect.value;
      const city = cityNames[code];
      $("alianca-orientacao").hidden = Boolean(city);
      $("alianca-resultado").hidden = !city;
      if (!city) return;
      $("alianca-localidade").textContent = city;
      const president = presidentSelect.value;
      const links = linksFor().filter((link) => !allySelect.value || allySelect.value === `${link.cargo}:${link.candidato}`);
      const national = municipalResult(presidentialPack, code, 1);
      const rows = links.map((link) => {
        const state = municipalResult(offices[link.cargo].registros, code, 1);
        const pVotes = national.votes[president] ?? 0;
        const sVotes = state.votes[link.candidato] ?? 0;
        const pValid = national.values[3];
        const sValid = state.values[3];
        const pRate = rate(pVotes, pValid);
        const sRate = rate(sVotes, sValid);
        return {link, pVotes, sVotes, pValid, sValid, pRate, sRate,
          voteGap: delta(pVotes, sVotes), shareGap: delta(pRate, sRate)};
      });
      if (sortSelect.value !== "office") {
        const direction = sortSelect.value === "high" ? -1 : 1;
        rows.sort((a, b) => {
          if (a.shareGap == null || b.shareGap == null) return Number(a.shareGap == null) - Number(b.shareGap == null);
          return direction * (a.shareGap - b.shareGap);
        });
      }
      $("alianca-linhas").innerHTML = rows.map((row) => `<tr role="row">
        <th scope="row" role="rowheader" class="paired-count">${mobileLabel(stateCandidate)}
          ${html(allyName(row.link))} · ${officeNames[row.link.cargo]}
          <br>${paired(row.sVotes, row.sRate, row.sValid)}
          <small class="alliance-note">${linkTypes(row.link)}</small></th>
        <td role="cell" class="paired-count">${mobileLabel(presidential)}${html(nameWithParty(alliances.presidencia[president]))}
          <br>${paired(row.pVotes, row.pRate, row.pValid)}</td>
        <td role="cell" class="paired-count">${mobileLabel(gapLabel)}${countWithRate(signed(row.voteGap), signed(row.shareGap, pointsUnit))}</td>
      </tr>`).join("");
      $("alianca-fontes").innerHTML = links.map((link) => `<li><strong>${html(allyName(link))}</strong> ·
        ${linkTypes(link)}<ul>
          ${link.apoio ? `<li>${dataLink(alliances.fontes[link.apoio])}</li>` : ""}
          ${link.formal ? `<li>${dataLink(alliances.fontes.tse)}</li>` : ""}
        </ul></li>`).join("");
      $("alianca-csv").onclick = () => {
        const headers = [t("Código TSE", "TSE code"), municipalName, presidential,
          t("Votos presidente", "Presidential votes"), t("Válidos presidente", "Valid presidential votes"),
          t("% presidente", "% president"), t("Cargo estadual", "State office"), candidate,
          t("Votos estadual", "State candidate votes"), t("Válidos estadual", "Valid votes for state office"),
          t("% estadual", "% state candidate"), t("Diferença em votos", "Difference in votes"),
          t("Diferença em pontos percentuais", "Difference in percentage points"),
          t("Vínculo", "Relationship"), t("Apoio público · fonte", "Public endorsement · source"),
          t("Apoio público · data", "Public endorsement · date"), t("Vínculo formal · fonte", "Formal link · source"),
          t("Vínculo formal · data", "Formal link · date")];
        const lines = rows.map(({link, pVotes, pValid, pRate, sVotes, sValid, sRate, voteGap, shareGap}) => {
          const support = alliances.fontes[link.apoio];
          const formal = link.formal ? alliances.fontes.tse : null;
          return [code, city, nameWithParty(alliances.presidencia[president]), pVotes, pValid, csvNumber(pRate),
            officeNames[link.cargo], allyName(link), sVotes, sValid, csvNumber(sRate), voteGap, csvNumber(shareGap),
            linkTypes(link), support?.url, support?.data, formal?.url, formal?.data];
        });
        downloadCsv([headers, ...lines], `atlas-RJ-2026-aliancas-${code}-${president}.csv`);
      };
    }

    function renderOffice() {
      const office = offices[officeSelect.value];
      const territory = statewide.checked ? "" : citySelect.value;
      statewide.disabled = !citySelect.value;
      const row = municipalResult(office.registros, territory, 1);
      const valid = row.values[3];
      $("rj-total-validos").textContent = `${cityNames[territory] || t("Total estadual", "Statewide total")} · ${n(valid)} ${t("votos válidos no cargo", "valid votes for this office")} ·
        ${t("Última totalização", "Last count")} ${formatDate(office.ultima_totalizacao)}`;
      $("rj-candidatos").innerHTML = Object.entries(office.candidatos).map(([code, info]) => ({
        info, votes: row.votes[code] ?? 0
      })).sort((a, b) => b.votes - a.votes || ordered.compare(a.info.nome, b.info.nome)).map(({info, votes}) => {
        const slate = info.coligacao === "PARTIDO ISOLADO" ? t("Partido isolado", "Party standing alone") :
          info.coligacao === "FEDERAÇÃO" ? info.federacao : info.coligacao;
        const excluded = !territory && votes === 0 && info.votos_nominais_uf > 0 ?
          `<small class="alliance-note">${n(info.votos_nominais_uf)} ${t("votos nominais excluídos dos válidos", "candidate votes excluded from valid votes")}</small>` : "";
        return `<tr role="row"><th scope="row" role="rowheader">${mobileLabel(candidate)}${html(nameWithParty(info))}</th>
          <td role="cell">${mobileLabel(registration)}${html(slate)}</td><td role="cell">${mobileLabel(countLabel)}${n(votes)}${excluded}</td>
          <td role="cell">${mobileLabel(shareLabel)}${pct(rate(votes, valid))}</td></tr>`;
      }).join("");
    }
    presidentSelect.addEventListener("change", () => { refreshAllies(); renderComparison(); });
    for (const control of [allySelect, sortSelect]) control.addEventListener("change", renderComparison);
    for (const control of [officeSelect, statewide]) control.addEventListener("change", renderOffice);
    function changeCity() {
      statewide.checked = false;
      renderComparison();
      renderOffice();
    }
    citySelect.addEventListener("change", changeCity);
    syncMunicipality = () => {
      if (cityNames[municipio.value] && municipio.value !== citySelect.value) {
        citySelect.value = municipio.value;
        changeCity();
      }
    };
    refreshAllies();
    renderComparison();
    renderOffice();
  }

  async function refreshTerritory() {
    const state = uf.value;
    stateLabel.hidden = !state;
    stateLabel.textContent = state ? `${state} · ${states[state]}` : "";
    target.hidden = state !== "RJ";
    if (!box.open) return;
    if (!state) {
      status.textContent = t("Selecione uma UF no Explorador.", "Select a state in the Explorer.");
      return;
    }
    if (state !== "RJ") {
      status.textContent = t("As alianças estão disponíveis para o RJ. Selecione RJ no Explorador para consultar.", "Alliance results are available for RJ. Select RJ in the Explorer to view them.");
      return;
    }
    if (ready) {
      status.textContent = "";
      return;
    }
    if (loading) {
      status.textContent = t("Carregando resultados do RJ…", "Loading RJ results…");
      return;
    }
    loading = true;
    status.textContent = t("Carregando resultados do RJ…", "Loading RJ results…");
    try {
      const [catalogue, president, governor, senate, alliances] = await Promise.all([
        fetchData("catalogo.json"), loadMunicipalPack(2026, "RJ"),
        fetchData("2026/governador/RJ/municipios.json"), fetchData("2026/senador/RJ/municipios.json"),
        fetchData("2026/aliancas/RJ/primeiro-turno.json")
      ]);
      if (uf.value !== "RJ") return;
      init(catalogue.uf.RJ, president, {governador: governor, senador: senate}, alliances);
      status.textContent = "";
      ready = true;
    } catch {
      target.replaceChildren();
      if (uf.value === "RJ") {
        status.textContent = t("Falha ao carregar os resultados. Feche e reabra esta seção para tentar novamente.", "Could not load the results. Close and reopen this section to try again.");
      }
    } finally {
      loading = false;
    }
  }
  function followAnchor() {
    if (location.hash === "#aliancas-rj") box.open = true;
    refreshTerritory();
  }
  box.addEventListener("toggle", refreshTerritory);
  document.addEventListener("atlas:territorychange", () => {
    if (uf.value === "RJ") syncMunicipality?.();
    refreshTerritory();
  });
  window.addEventListener("hashchange", followAnchor);
  followAnchor();
})();
