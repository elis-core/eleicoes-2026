"use strict";
(() => {
  const field = document.querySelector('#document-search');
  const cards = [...document.querySelectorAll('.document-card')];
  const count = document.querySelector('#document-count');
  if (!field || !count) return;
  const normalize = text => text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
  const filter = () => {
    const query = normalize(field.value.trim());
    for (const card of cards) card.hidden = !normalize(card.dataset.search).includes(query);
    count.textContent = `${cards.filter(card => !card.hidden).length} de ${cards.length} etapas`;
  };
  field.closest('.documents-filter').hidden = false;
  field.addEventListener('input', filter);
  filter();
})();
