/**
 * Wyszukiwarka ulic z normalizacją polskich znaków i dopasowaniem przyrostkowym/rozmytym
 */

class StreetSearch {
  constructor(streets, onSelect) {
    this.streets = streets;
    this.onSelect = onSelect;
    this.selectedIndex = -1;
    this.results = [];

    this.inputEl = document.getElementById('search-input');
    this.resultsEl = document.getElementById('search-results');
    this.clearBtn = document.getElementById('clear-search-btn');

    this.initEvents();
  }

  // Normalizacja tekstu (usuwanie polskich znaków diakrytycznych i małe litery)
  static normalize(str) {
    if (!str) return '';
    return str
      .toLowerCase()
      .trim()
      .replace(/ą/g, 'a')
      .replace(/ć/g, 'c')
      .replace(/ę/g, 'e')
      .replace(/ł/g, 'l')
      .replace(/ń/g, 'n')
      .replace(/ó/g, 'o')
      .replace(/ś/g, 's')
      .replace(/ź/g, 'z')
      .replace(/ż/g, 'z')
      .replace(/^ul\.\s*|^ulica\s*|^al\.\s*|^aleja\s*|^plac\s*|^pl\.\s*|^osiedle\s*|^os\.\s*|^park\s*|^bulwar\s*|^most\s*|^kładka\s*|^kladka\s*/, '');
  }

  initEvents() {
    this.inputEl.addEventListener('input', (e) => {
      this.handleSearch(e.target.value);
    });

    this.inputEl.addEventListener('keydown', (e) => {
      this.handleKeydown(e);
    });

    this.inputEl.addEventListener('focus', () => {
      if (this.inputEl.value.trim().length > 0) {
        this.resultsEl.classList.remove('hidden');
      }
    });

    this.clearBtn.addEventListener('click', () => {
      this.clearSearch();
    });

    // Zamknij podpowiedzi po kliknięciu poza wyszukiwarką
    document.addEventListener('click', (e) => {
      if (!this.inputEl.contains(e.target) && !this.resultsEl.contains(e.target)) {
        this.resultsEl.classList.add('hidden');
      }
    });

    // Reagowanie na zmianę języka
    window.addEventListener('languagechange', () => {
      if (this.results.length > 0) {
        this.renderResults();
      }
    });
  }

  handleSearch(query) {
    const normQuery = StreetSearch.normalize(query);
    if (!normQuery) {
      this.resultsEl.classList.add('hidden');
      this.clearBtn.classList.add('hidden');
      this.results = [];
      this.selectedIndex = -1;
      return;
    }

    this.clearBtn.classList.remove('hidden');

    const i18n = window.krakowI18n;

    // Filtrowanie i punktacja dopasowania (uwzględnia wersję polską, zlokalizowaną i dosłowne znaczenie)
    this.results = this.streets
      .map(street => {
        const p = street.properties;
        const plName = typeof p.name === 'object' ? (p.name.pl || '') : (p.name || '');
        const locName = i18n ? i18n.localize(p.name) : plName;
        const plFullName = typeof p.full_name === 'object' ? (p.full_name.pl || '') : (p.full_name || '');
        const locFullName = i18n ? i18n.localize(p.full_name) : plFullName;
        const literalMeaning = p.literal_meaning ? (i18n ? i18n.localize(p.literal_meaning) : (p.literal_meaning.en || '')) : '';
        const etymology = i18n ? i18n.localize(p.etymology) : (typeof p.etymology === 'object' ? p.etymology.pl : (p.etymology || ''));

        const normPlName = StreetSearch.normalize(plName);
        const normLocName = StreetSearch.normalize(locName);
        const normPlFullName = StreetSearch.normalize(plFullName);
        const normLocFullName = StreetSearch.normalize(locFullName);
        const decomFormer = p.dekomunizacja_1991?.former_description || '';
        const prlName = p.prl_1951_1955?.official_name || '';
        const naziName = p.okupacja_1940_1941?.official_name || '';

        const normDecomFormer = StreetSearch.normalize(decomFormer);
        const normPrlName = StreetSearch.normalize(prlName);
        const normNaziName = StreetSearch.normalize(naziName);

        let score = 0;
        let matchedHistorical = null;

        if (normPlName.startsWith(normQuery) || normLocName.startsWith(normQuery)) {
          score = 100 - Math.min(normPlName.length, normLocName.length) + normQuery.length;
        } else if (normLiteral && normLiteral.startsWith(normQuery)) {
          score = 90;
        } else if (normPlName.includes(normQuery) || normLocName.includes(normQuery)) {
          score = 70;
        } else if (normLiteral && normLiteral.includes(normQuery)) {
          score = 65;
        } else if (normDecomFormer && normDecomFormer.includes(normQuery)) {
          score = 60;
          matchedHistorical = `d. ${decomFormer}`;
        } else if (normPrlName && normPrlName.includes(normQuery)) {
          score = 58;
          matchedHistorical = `w PRL: ${prlName}`;
        } else if (normNaziName && normNaziName.includes(normQuery)) {
          score = 56;
          matchedHistorical = `1940: ${naziName}`;
        } else if (normPlFullName.includes(normQuery) || normLocFullName.includes(normQuery)) {
          score = 50;
        } else if (normEtymology.includes(normQuery)) {
          score = 20;
        }

        return { street, score, matchedHistorical };
      })
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 7)
      .map(item => {
        item.street._matchedHistorical = item.matchedHistorical;
        return item.street;
      });

    this.renderResults();
  }

  renderResults() {
    const i18n = window.krakowI18n;

    if (this.results.length === 0) {
      this.resultsEl.innerHTML = `
        <div class="px-4 py-3 text-sm text-slate-500 text-center">
          ${i18n ? i18n.t('no_results') : 'Nie znaleziono ulicy o podanej nazwie'}
        </div>
      `;
      this.resultsEl.classList.remove('hidden');
      return;
    }

    this.resultsEl.innerHTML = this.results.map((street, idx) => {
      const p = street.properties;
      const isSelected = idx === this.selectedIndex;
      const rawName = i18n ? i18n.localize(p.name, '') : (p.name?.pl || p.name || '');
      const displayName = i18n ? i18n.localize(p.full_name, rawName) : (p.full_name?.pl || p.full_name || rawName);
      const safeName = displayName.replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

      let badgeHtml = '';
      if (p.is_landmark) {
        if (p.landmark_group === 'estates') {
          badgeHtml = '<span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">Osiedle</span>';
        } else if (p.landmark_group === 'parks') {
          badgeHtml = '<span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">Park</span>';
        } else {
          badgeHtml = '<span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-100 text-cyan-800 border border-cyan-200">Most / Kładka</span>';
        }
      }

      const historicalHtml = street._matchedHistorical 
        ? `<div class="text-[11px] text-amber-700 font-medium pl-6 truncate"><span class="italic text-slate-400 font-normal">Historia:</span> ${street._matchedHistorical}</div>` 
        : '';

      return `
        <div class="search-item px-4 py-2.5 cursor-pointer border-b border-slate-100 last:border-0 ${isSelected ? 'selected' : ''}" data-idx="${idx}">
          <div class="flex items-center justify-between gap-2">
            <div class="font-semibold text-slate-800 text-sm flex items-center gap-2 min-w-0">
              <svg class="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
              </svg>
              <span class="truncate">${safeName}</span>
            </div>
            ${badgeHtml}
          </div>
          ${historicalHtml}
        </div>
      `;
    }).join('');

    // Dodanie nasłuchiwania na kliknięcie w wiersz
    this.resultsEl.querySelectorAll('.search-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-idx'), 10);
        this.selectStreet(this.results[idx]);
      });
    });

    this.resultsEl.classList.remove('hidden');
  }

  handleKeydown(e) {
    if (this.results.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex + 1) % this.results.length;
      this.updateSelectionUI();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex - 1 + this.results.length) % this.results.length;
      this.updateSelectionUI();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (this.selectedIndex >= 0 && this.selectedIndex < this.results.length) {
        this.selectStreet(this.results[this.selectedIndex]);
      } else if (this.results.length > 0) {
        this.selectStreet(this.results[0]);
      }
    } else if (e.key === 'Escape') {
      this.resultsEl.classList.add('hidden');
    }
  }

  updateSelectionUI() {
    const items = this.resultsEl.querySelectorAll('.search-item');
    items.forEach((item, idx) => {
      if (idx === this.selectedIndex) {
        item.classList.add('selected');
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.classList.remove('selected');
      }
    });
  }

  selectStreet(street) {
    const i18n = window.krakowI18n;
    const p = street.properties;
    const rawName = i18n ? i18n.localize(p.name, '') : (p.name?.pl || p.name || '');
    const fallbackName = p.is_landmark ? rawName : (rawName ? `ulica ${rawName}` : '');
    this.inputEl.value = i18n ? i18n.localize(p.full_name, fallbackName) : (p.full_name?.pl || p.full_name || fallbackName);
    this.resultsEl.classList.add('hidden');
    this.selectedIndex = -1;
    if (this.onSelect) {
      this.onSelect(street);
    }
  }

  clearSearch() {
    this.inputEl.value = '';
    this.clearBtn.classList.add('hidden');
    this.resultsEl.classList.add('hidden');
    this.results = [];
    this.selectedIndex = -1;
  }
}
