/**
 * Cracoscope – Cyfrowe Archiwum Aktów Toponimicznych Krakowa
 * Hub obsługujący 8 historycznych aktów:
 * 1. DRK 1880 – Wielka Regulacja Autonomiczna
 * 2. DRK 1912 – Wielki Kraków (14 gmin)
 * 3. Podgórze 1917 – Unifikacja nazw po połączeniu miast
 * 4. DRK 1926–1933 – Międzywojenny Modernizm II RP
 * 5. Okupacja 1940–1941 – Germanizacja Toponimii
 * 6. PRL 1951–1955 – Nowa Huta i Stalinizacja
 * 7. Rozszerzenie 1973–1975 – Drugie Wielkie Rozszerzenie
 * 8. Dekomunizacja 1991 – Uchwała RMK XXV/170/91
 */

class CracoscopeSourcesHub {
  constructor() {
    this.catalog = [];
    this.activeDocId = 'drk_1912';
    this.currentData = null;
    this.cache = {};
    this.activeView = 'table';
    this.searchQuery = '';
    this.activeDistrict = 'all';

    document.addEventListener('DOMContentLoaded', () => this.init());
  }

  async init() {
    const urlParams = new URLSearchParams(window.location.search);
    const requestedDoc = urlParams.get('doc');

    await this.loadCatalog();

    if (requestedDoc && this.catalog.some(d => d.id === requestedDoc)) {
      this.activeDocId = requestedDoc;
    } else {
      this.activeDocId = 'drk_1912';
    }

    this.renderDocumentTabs();
    await this.loadActiveDocument();
    this.setupEventListeners();

    this.handleHash();
    window.addEventListener('hashchange', () => this.handleHash());
  }

  async loadCatalog() {
    try {
      const resp = await fetch('data/sources/catalog.json');
      if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
      this.catalog = await resp.json();
    } catch (err) {
      console.error('Błąd ładowania katalogu źródeł:', err);
    }
  }

  getDocBadge(doc) {
    return `<span class="w-1.5 h-1.5 rounded-full bg-current opacity-75 mr-1.5"></span>`;
  }

  renderDocumentTabs() {
    const container = document.getElementById('document-selector-tabs');
    if (!container) return;

    container.innerHTML = this.catalog.map(doc => {
      const isActive = doc.id === this.activeDocId;
      const activeClass = isActive 
        ? 'bg-blue-600 text-white border-blue-600 shadow-sm ring-2 ring-blue-500/20' 
        : 'bg-white text-slate-700 hover:bg-slate-50 border-slate-200';

      return `
        <button 
          data-doc-id="${doc.id}" 
          class="doc-tab-btn flex flex-col text-left p-2 sm:p-2.5 rounded-xl border transition-all ${activeClass}"
        >
          <div class="flex items-center justify-between w-full">
            <span class="text-xs font-extrabold flex items-center truncate">
              ${this.getDocBadge(doc)}
              <span>${doc.year}</span>
            </span>
            <span class="text-[9px] font-bold px-1 py-0.5 rounded ${isActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'}">
              ${doc.streets_count}
            </span>
          </div>
          <span class="text-[10px] sm:text-[11px] mt-1 ${isActive ? 'text-blue-100' : 'text-slate-600'} font-semibold truncate leading-tight">
            ${doc.short_title || doc.title}
          </span>
        </button>
      `;
    }).join('');

    container.querySelectorAll('.doc-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetDocId = btn.dataset.docId;
        if (targetDocId !== this.activeDocId) {
          this.switchDocument(targetDocId);
        }
      });
    });
  }

  async switchDocument(docId) {
    this.activeDocId = docId;
    this.searchQuery = '';
    this.activeDistrict = 'all';

    const url = new URL(window.location);
    url.searchParams.set('doc', docId);
    window.history.pushState({}, '', url);

    this.renderDocumentTabs();
    await this.loadActiveDocument();

    const searchInput = document.getElementById('archive-search');
    if (searchInput) searchInput.value = '';

    this.switchView('table');
  }

  async loadActiveDocument() {
    if (this.cache[this.activeDocId]) {
      this.currentData = this.cache[this.activeDocId];
      this.renderDocumentContent();
      return;
    }

    try {
      const docMeta = this.catalog.find(d => d.id === this.activeDocId);
      const filePath = docMeta?.file || `data/sources/${this.activeDocId}.json`;
      const resp = await fetch(filePath);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      this.currentData = await resp.json();
      this.cache[this.activeDocId] = this.currentData;
      this.renderDocumentContent();
    } catch (err) {
      console.error('Błąd wczytywania dokumentu:', err);
    }
  }

  renderDocumentContent() {
    if (!this.currentData) return;

    this.renderHero();
    this.renderDistrictNav();
    this.renderParallelTable();
    this.renderHistoricalContext();
  }

  renderHero() {
    const meta = this.currentData.metadata || {};
    const stats = meta.stats || {
      total_streets: this.currentData.streets?.length || 0,
      matched_contemporary: this.currentData.streets?.filter(s => s.geojson_id)?.length || 0,
      coverage: 'Kraków'
    };

    const badgeContainer = document.getElementById('doc-badge-container');
    if (badgeContainer) {
      badgeContainer.innerHTML = `
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200">
          <span>${meta.era || 'Akt toponimiczny'} • ${meta.year || ''}</span>
        </div>
      `;
    }

    const titleEl = document.getElementById('doc-title');
    if (titleEl) titleEl.textContent = meta.title || 'Akt Archiwalny';

    const subEl = document.getElementById('doc-subtitle');
    if (subEl) subEl.textContent = meta.subtitle || meta.legal_basis || '';

    const topbarLink = document.getElementById('topbar-source-link');
    const topbarLabel = document.getElementById('topbar-source-label');
    if (topbarLink && meta.pdf_url) {
      topbarLink.href = meta.pdf_url;
      topbarLink.style.display = '';
      if (topbarLabel) {
        if (this.activeDocId === 'dekomunizacja_1991' || this.activeDocId === 'prl_1951_1955' || this.activeDocId === 'rozszerzenie_1973_1975') {
          topbarLabel.textContent = 'BIP Kraków ↗';
        } else {
          topbarLabel.textContent = 'Skan JBC (PDF) ↗';
        }
      }
    }

    const tableTabLabel = document.getElementById('view-tab-table-label');
    if (tableTabLabel) {
      tableTabLabel.textContent = `Wykaz ulic (${stats.total_streets})`;
    }
  }

  renderDistrictNav() {
    const navContainer = document.getElementById('district-pills-container');
    if (!navContainer || !this.currentData) return;

    const districts = [];
    const seen = new Set();
    for (const item of this.currentData.streets || []) {
      const dId = item.district_id || '–';
      const dName = item.district_name || dId;
      const key = `${dId}__${dName}`;
      if (!seen.has(key)) {
        seen.add(key);
        districts.push({ id: dId, name: dName });
      }
    }

    let pillsHtml = `
      <button 
        data-district="all" 
        class="district-pill flex-shrink-0 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${this.activeDistrict === 'all' ? 'bg-blue-600 text-white shadow-xs' : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'}"
      >
        Wszystkie dzielnice (${this.currentData.streets?.length || 0})
      </button>
    `;

    for (const d of districts) {
      const count = (this.currentData.streets || []).filter(s => (s.district_id || '–') === d.id).length;
      const isActive = this.activeDistrict === d.id;
      const label = d.name !== d.id ? `${d.id} ${d.name}` : d.name;

      pillsHtml += `
        <button 
          data-district="${this.escapeHtml(d.id)}" 
          class="district-pill flex-shrink-0 px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${isActive ? 'bg-blue-600 text-white font-bold shadow-xs' : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'}"
        >
          ${this.escapeHtml(label)} <span class="opacity-70 text-[10px]">(${count})</span>
        </button>
      `;
    }

    navContainer.innerHTML = pillsHtml;

    navContainer.querySelectorAll('.district-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        this.activeDistrict = e.currentTarget.dataset.district;
        this.renderDistrictNav();
        this.filterTable();
      });
    });
  }

  getFilteredStreets() {
    if (!this.currentData || !this.currentData.streets) return [];
    let list = this.currentData.streets;

    if (this.activeDistrict !== 'all') {
      list = list.filter(s => (s.district_id || '–') === this.activeDistrict);
    }

    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(s => {
        const off = (s.official_name || s.official_name_1912 || s.official_name_1880 || s.official_name_1917 || s.official_name_1926 || s.official_name_1940 || s.official_name_1951 || s.official_name_1973 || s.official_name_1991 || s.target_street_name || '').toLowerCase();
        const fmr = (s.former_description || '').toLowerCase();
        const cur = (s.current_full_name || '').toLowerCase();
        const dist = (s.district_name || '').toLowerCase();
        const note = (s.note || '').toLowerCase();
        return off.includes(q) || fmr.includes(q) || cur.includes(q) || dist.includes(q) || note.includes(q);
      });
    }

    return list;
  }

  renderParallelTable() {
    const container = document.getElementById('parallel-table-container');
    if (!container) return;

    const streets = this.getFilteredStreets();

    const countEl = document.getElementById('search-matches-count');
    if (countEl) {
      const total = this.currentData.streets?.length || 0;
      countEl.textContent = `${streets.length} z ${total}`;
    }

    if (streets.length === 0) {
      container.innerHTML = `
        <div class="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 shadow-xs">
          <div class="w-10 h-10 mx-auto mb-3 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
          <h4 class="font-bold text-slate-800 text-sm">Nie znaleziono pozycji w tym dokumencie</h4>
          <p class="text-xs text-slate-500 mt-1">Zmień kryteria wyszukiwania lub zresetuj filtr dzielnic.</p>
        </div>
      `;
      return;
    }

    const docId = this.activeDocId;
    let col1Header = 'Nazwa uchwalona';
    let col2Header = 'Dawne określenie / nazwa historyczna';
    let col3Header = 'Dzielnica i tło historyczne';

    if (docId === 'drk_1880') {
      col1Header = 'Nazwa uregulowana (1880)';
      col2Header = 'Dawne miano / zabór austriacki';
      col3Header = 'Dzielnica i tło autonomiczne';
    } else if (docId === 'drk_1912') {
      col1Header = 'Nazwa uchwalona (1912)';
      col2Header = 'Dawne określenie podkrakowskie';
      col3Header = 'Dzielnica i uzasadnienie';
    } else if (docId === 'podgorze_1917') {
      col1Header = 'Nowa nazwa podgórska (1917)';
      col2Header = 'Zdublowana dawna nazwa';
      col3Header = 'Dzielnica XXI Podgórze';
    } else if (docId === 'drk_1926_1933') {
      col1Header = 'Nazwa modernistyczna (II RP)';
      col2Header = 'Dawne przeznaczenie / wał forteczny';
      col3Header = 'Dzielnica i modernizm II RP';
    } else if (docId === 'okupacja_1940_1941') {
      col1Header = 'Zniemczona nazwa (1940–1941)';
      col2Header = 'Polska nazwa przed 1940 r.';
      col3Header = 'Dzielnica i kontekst okupacyjny';
    } else if (docId === 'prl_1951_1955') {
      col1Header = 'Nazwa nadana w PRL (1951–1955)';
      col2Header = 'Dawne miano / przed przemianowaniem';
      col3Header = 'Dzielnica i kontekst socrealizmu';
    } else if (docId === 'rozszerzenie_1973_1975') {
      col1Header = 'Nazwa nadana po przyłączeniu (1973)';
      col2Header = 'Dawna nazwa wiejska / zdublowana';
      col3Header = 'Przyłączona miejscowość';
    } else if (docId === 'dekomunizacja_1991') {
      col1Header = 'Nazwa przywrócona / nadana (1991)';
      col2Header = 'Nazwa okresu PRL (usunięta)';
      col3Header = 'Dzielnica i powrót do tradycji';
    }

    let rowsHtml = '';
    for (const s of streets) {
      const officialName = s.official_name || s.official_name_1912 || s.official_name_1880 || s.official_name_1917 || s.official_name_1926 || s.official_name_1940 || s.official_name_1951 || s.official_name_1973 || s.official_name_1991 || s.target_street_name || s.current_full_name || '–';
      const formerName = s.former_description || s.current_full_name || '–';
      const geoId = s.geojson_id;
      const isActive = !!geoId;
      const districtLabel = s.district_name ? `${s.district_id ? s.district_id + ' • ' : ''}${s.district_name}` : (s.district_id || '–');

      let debateBadge = '';
      if (s.council_debate) {
        debateBadge = `
          <button 
            onclick="window.sourcesHub.openDebateModal('${s.id}')"
            class="inline-flex items-center gap-1 mt-1 text-[11px] font-bold text-amber-700 hover:text-amber-900 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-2 py-0.5 rounded-md transition-colors"
          >
            <span>Debata: ${this.escapeHtml(s.council_debate.speaker)}</span>
          </button>
        `;
      }

      let noteHtml = '';
      if (s.note) {
        noteHtml = `<p class="text-xs text-slate-600 mt-1 leading-snug">${this.escapeHtml(s.note)}</p>`;
      }

      let mapBtn = '';
      if (isActive) {
        mapBtn = `
          <a 
            href="index.html?street=${encodeURIComponent(geoId)}" 
            class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-all shadow-xs flex-shrink-0"
            title="Pokaż bieg tej ulicy na interaktywnej mapie Krakowa"
          >
            <span>Mapa</span>
          </a>
        `;
      } else {
        mapBtn = `
          <span class="inline-flex items-center text-[10px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md flex-shrink-0">
            Historyczna
          </span>
        `;
      }

      const isHighlightCol = docId === 'dekomunizacja_1991' || docId === 'prl_1951_1955' || docId === 'okupacja_1940_1941';

      rowsHtml += `
        <tr id="row-${s.id}" data-ref-id="${s.id}" data-geo-id="${geoId || ''}" class="hover:bg-slate-50/80 transition-colors border-b border-slate-200/80 group">
          
          <td class="p-3.5 align-top">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-slate-300'} flex-shrink-0"></span>
              <span class="font-bold text-slate-900 text-sm group-hover:text-blue-600 transition-colors">
                ${this.escapeHtml(officialName)}
              </span>
            </div>
            ${s.current_full_name && s.current_full_name !== officialName ? `<div class="text-[11px] text-slate-500 font-normal mt-0.5 ml-4">Dziś: <span class="font-semibold text-slate-700">${this.escapeHtml(s.current_full_name)}</span></div>` : ''}
            ${debateBadge}
          </td>

          <td class="p-3.5 align-top">
            <div class="text-xs font-semibold ${isHighlightCol ? 'text-red-700 bg-red-50/70 border border-red-200 px-2 py-1 rounded-md' : 'text-slate-700'}">
              ${this.escapeHtml(formerName)}
            </div>
          </td>

          <td class="p-3.5 align-top">
            <span class="inline-flex items-center text-[11px] font-bold text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-md">
              ${this.escapeHtml(districtLabel)}
            </span>
            ${noteHtml}
          </td>

          <td class="p-3.5 align-top text-right">
            ${mapBtn}
          </td>

        </tr>
      `;
    }

    container.innerHTML = `
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse min-w-[640px]">
            <thead>
              <tr class="bg-slate-100/80 border-b border-slate-200 text-[11px] font-extrabold uppercase tracking-wider text-slate-500">
                <th class="p-3.5">${col1Header}</th>
                <th class="p-3.5">${col2Header}</th>
                <th class="p-3.5">${col3Header}</th>
                <th class="p-3.5 text-right">Mapa</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              ${rowsHtml}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  renderHistoricalContext() {
    const container = document.getElementById('context-content-area');
    if (!container) return;

    const meta = this.currentData?.metadata || {};
    const ctx = this.currentData?.historical_context || {};

    container.innerHTML = `
      <div>
        <span class="text-xs font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-100">
          ${this.escapeHtml(meta.era || 'Kontekst historyczny')}
        </span>
        <h3 class="text-xl font-bold text-slate-900 mt-3 mb-2">
          ${this.escapeHtml(meta.title || 'Akt Toponimiczny')}
        </h3>
        <p class="text-sm text-slate-600 leading-relaxed">
          ${this.escapeHtml(ctx.intro || meta.subtitle || '')}
        </p>
      </div>

      ${(this.currentData.debates || []).filter(d => d.summary || d.quote || d.content || d.decision || d.outcome).map(d => `
        <article class="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
          <h4 class="font-bold text-slate-900">${this.escapeHtml(d.title || d.topic || 'Kontekst uchwały')}</h4>
          <p class="text-xs text-slate-500">${this.escapeHtml([d.speaker, d.date, d.page_printed ? `s. ${d.page_printed}` : ''].filter(Boolean).join(' • '))}</p>
          ${d.summary || d.quote || d.content ? `<p class="text-sm text-slate-700 leading-relaxed">${this.escapeHtml(d.summary || d.quote || d.content)}</p>` : ''}
          ${d.decision || d.outcome ? `<p class="text-sm text-slate-700 leading-relaxed">${this.escapeHtml(d.decision || d.outcome)}</p>` : ''}
        </article>
      `).join('')}

      ${ctx.solution ? `
        <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-700 leading-relaxed space-y-2">
          <h4 class="font-bold text-slate-900">Istota reformy toponimicznej</h4>
          <p>${this.escapeHtml(ctx.solution)}</p>
        </div>
      ` : ''}

      ${ctx.milestone ? `
        <div class="p-4 rounded-xl bg-amber-50/60 border border-amber-200 text-sm text-slate-800 leading-relaxed space-y-1">
          <h5 class="font-bold text-amber-950">Znaczenie dla Krakowa</h5>
          <p>${this.escapeHtml(ctx.milestone)}</p>
        </div>
      ` : ''}

      <div class="p-5 rounded-xl bg-blue-50/60 border border-blue-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h5 class="font-bold text-slate-900 text-sm">${this.escapeHtml(meta.subtitle || 'Oficjalna publikacja')}</h5>
          <p class="text-xs text-slate-600 mt-0.5">${this.escapeHtml(meta.legal_basis || '')}</p>
        </div>
        <div class="flex items-center gap-2">
          <a href="${meta.jbc_url || meta.pdf_url || '#'}" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors shadow-xs">
            Zobacz źródło cyfrowe ↗
          </a>
        </div>
      </div>
    `;
  }

  setupEventListeners() {
    const searchInput = document.getElementById('archive-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.trim().toLowerCase();
        this.filterTable();
      });
    }

    const viewBtns = document.querySelectorAll('.view-toggle-btn');
    viewBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = e.currentTarget.dataset.view;
        this.switchView(view);
      });
    });
  }

  switchView(view) {
    this.activeView = view;
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
      const isActive = btn.dataset.view === view;
      btn.classList.toggle('active', isActive);
      if (isActive) {
        btn.className = 'view-toggle-btn active px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-bold transition-all bg-white text-blue-700 shadow-xs';
      } else {
        btn.className = 'view-toggle-btn px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-slate-600 hover:text-slate-900 transition-all';
      }
    });

    const toolbar = document.getElementById('archive-toolbar');
    if (toolbar) {
      toolbar.style.display = (view === 'table') ? '' : 'none';
    }

    document.getElementById('view-table')?.classList.toggle('hidden', view !== 'table');
    document.getElementById('view-context')?.classList.toggle('hidden', view !== 'context');
  }

  filterTable() {
    this.renderParallelTable();
  }

  handleHash() {
    const hash = window.location.hash.replace(/^#/, '');
    if (!hash) return;

    this.switchView('table');

    setTimeout(() => {
      let targetRow = document.querySelector(`tr[data-ref-id="${hash}"]`);
      if (!targetRow) {
        targetRow = document.querySelector(`tr[data-geo-id="${hash}"]`);
      }
      if (!targetRow) {
        targetRow = document.getElementById(`row-${hash}`);
      }

      if (targetRow) {
        targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetRow.classList.add('row-highlight');
      }
    }, 250);
  }

  openDebateModal(streetId) {
    const street = (this.currentData?.streets || []).find(s => s.id === streetId);
    if (!street || !street.council_debate) return;

    const d = street.council_debate;
    alert(`Stenogram debaty Rady Miasta: ${street.official_name || street.official_name_1880 || street.official_name_1917 || street.official_name_1926 || street.official_name_1940 || street.official_name_1951 || street.official_name_1973 || street.official_name_1991}\nMówca: ${d.speaker}\n\n"${d.quote}"`);
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

window.sourcesHub = new CracoscopeSourcesHub();
