/**
 * Obsługa podstrony Cyfrowego Archiwum DRK 1912 (drk1912.html)
 * Spójny, nowoczesny interfejs Cracoscope
 */

class DrkArchivePage {
  constructor() {
    this.data = null;
    this.activeView = 'table'; // 'table' | 'debates' | 'facsimiles'
    this.searchQuery = '';
    this.activeDistrict = 'all';

    document.addEventListener('DOMContentLoaded', () => this.init());
  }

  async init() {
    await this.loadData();
    if (!this.data) return;

    this.renderDistrictNav();
    this.renderParallelTable();
    this.renderDebates();
    this.setupEventListeners();

    // Sprawdź czy URL ma hash (np. #drk1912_dxvii_w_jtowska lub #wojtowska)
    this.handleInitialHash();
    window.addEventListener('hashchange', () => this.handleInitialHash());
  }

  async loadData() {
    try {
      const resp = await fetch('data/sources/drk_1912.json');
      if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
      this.data = await resp.json();
    } catch (err) {
      console.error('Błąd ładowania danych archiwalnych:', err);
      const container = document.getElementById('archive-content-area');
      if (container) {
        container.innerHTML = `
          <div class="p-8 text-center text-red-700 bg-red-50 border border-red-200 rounded-2xl">
            <h3 class="text-base font-bold">Błąd ładowania bazy archiwalnej</h3>
            <p class="text-xs mt-1 text-red-600">${err.message}</p>
          </div>
        `;
      }
    }
  }

  setupEventListeners() {
    // Wyszukiwarka
    const searchInput = document.getElementById('archive-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.trim().toLowerCase();
        this.filterTable();
      });
    }

    // Przełącznik widoków (Tabela / Debata / Informacje)
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
    document.getElementById('view-debates')?.classList.toggle('hidden', view !== 'debates');
    document.getElementById('view-facsimiles')?.classList.toggle('hidden', view !== 'facsimiles');

    // Płynny powrót do góry treści
    window.scrollTo({ top: 220, behavior: 'smooth' });
  }

  renderDistrictNav() {
    const navContainer = document.getElementById('district-pills-container');
    if (!navContainer || !this.data) return;

    const districts = [];
    const seen = new Set();
    for (const item of this.data.streets) {
      if (!seen.has(item.district_id)) {
        seen.add(item.district_id);
        districts.push({ id: item.district_id, name: item.district_name });
      }
    }

    const baseClass = "district-nav-pill px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border shadow-xs cursor-pointer";
    const activeClass = "bg-blue-600 text-white border-blue-600";
    const inactiveClass = "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900";

    let html = `
      <a href="#all" onclick="window.drkPage.filterDistrict('all', event)" class="${baseClass} ${activeClass}">
        Wszystkie dzielnice (166)
      </a>
    `;

    districts.forEach(d => {
      html += `
        <a href="#district-${d.id.toLowerCase()}" onclick="window.drkPage.filterDistrict('${d.id}', event)" class="${baseClass} ${inactiveClass}">
          ${d.id}. ${d.name}
        </a>
      `;
    });

    navContainer.innerHTML = html;
  }

  filterDistrict(distId, e) {
    if (e) e.preventDefault();
    this.activeDistrict = distId;

    const baseClass = "district-nav-pill px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border shadow-xs cursor-pointer";
    const activeClass = "bg-blue-600 text-white border-blue-600";
    const inactiveClass = "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900";

    document.querySelectorAll('.district-nav-pill').forEach(pill => {
      const isAll = distId === 'all' && pill.getAttribute('href') === '#all';
      const isMatch = pill.getAttribute('href') === `#district-${distId.toLowerCase()}`;
      const isActive = isAll || isMatch;
      pill.className = `${baseClass} ${isActive ? activeClass : inactiveClass}`;
    });

    if (distId === 'all') {
      document.querySelectorAll('.district-block').forEach(b => b.style.display = '');
    } else {
      document.querySelectorAll('.district-block').forEach(b => {
        const bDist = b.dataset.districtId;
        b.style.display = (bDist === distId) ? '' : 'none';
      });
      // Przewiń do nagłówka danej dzielnicy
      const targetHeader = document.getElementById(`district-${distId.toLowerCase()}`);
      if (targetHeader) {
        targetHeader.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  renderParallelTable() {
    const tableContainer = document.getElementById('parallel-table-container');
    if (!tableContainer || !this.data) return;

    // Grupuj ulice wg dzielnicy
    const grouped = {};
    this.data.streets.forEach(s => {
      if (!grouped[s.district_id]) {
        grouped[s.district_id] = {
          id: s.district_id,
          name: s.district_name,
          streets: []
        };
      }
      grouped[s.district_id].streets.push(s);
    });

    let html = '';

    for (const distKey in grouped) {
      const group = grouped[distKey];
      html += `
        <div class="district-block bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden mb-6" data-district-id="${group.id}">
          <header id="district-${group.id.toLowerCase()}" class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2">
            <h3 class="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
              <span>Dzielnica ${group.id}. „${group.name}”</span>
              <span class="text-[11px] font-semibold text-slate-600 bg-slate-200/80 px-2 py-0.5 rounded-md">
                ${group.streets.length} uchwalonych ulic
              </span>
            </h3>
            <span class="text-xs text-slate-500 hidden sm:inline">
              Włączona do Wielkiego Krakowa 1910–1912
            </span>
          </header>

          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-slate-50/75 border-b border-slate-200 text-slate-500 text-[11px] font-bold uppercase tracking-wider">
                  <th class="w-5/12 p-3.5 sm:p-4">Dotychczasowa nazwa / opis przebiegu w 1912 r.</th>
                  <th class="w-5/12 p-3.5 sm:p-4">Uchwała Rady: Nowa nazwa urzędowa</th>
                  <th class="w-2/12 p-3.5 sm:p-4 text-right">Nawigacja</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
      `;

      group.streets.forEach(item => {
        const isHistorical = !item.is_active;

        html += `
          <tr 
            id="${item.id}"
            data-geojson-id="${item.geojson_id || ''}"
            data-search-text="${(item.official_name_1912 + ' ' + item.former_description + ' ' + item.target_street_name + ' ' + (item.note || '')).toLowerCase()}"
            class="parallel-row hover:bg-slate-50/80 transition-colors"
          >
            <!-- Kolumna 1: Dawna nazwa / opis -->
            <td class="p-3.5 sm:p-4 align-top w-5/12">
              <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Dawny trakt / opis przebiegu:</div>
              <div class="text-xs sm:text-sm text-slate-800 font-medium leading-relaxed italic">„${item.former_description}”</div>
            </td>

            <!-- Kolumna 2: Nowa nazwa uchwalona 17 lipca 1912 r. -->
            <td class="p-3.5 sm:p-4 align-top w-5/12">
              <div class="text-sm sm:text-base font-extrabold text-slate-900 leading-snug">
                ${item.official_name_1912}
              </div>

              <div class="mt-1.5 flex items-center gap-1.5 flex-wrap">
                <span class="text-[10px] font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  DRK s. ${item.page_printed}
                </span>
                ${isHistorical ? `
                  <span class="text-[10px] font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Dawny trakt (wchłonięty)
                  </span>
                ` : `
                  <span class="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Współczesna: <strong>${item.current_full_name}</strong>
                  </span>
                `}
              </div>

              ${item.note ? `
                <div class="mt-2 text-xs text-amber-900 bg-amber-50/70 p-2 rounded-lg border border-amber-200/70">
                  ${item.note}
                </div>
              ` : ''}

              ${item.council_debate ? `
                <div class="mt-2 text-xs text-indigo-950 bg-indigo-50/80 p-2.5 rounded-lg border border-indigo-100 leading-snug">
                  <strong>Debata Rady:</strong> ${item.council_debate}
                </div>
              ` : ''}
            </td>

            <!-- Kolumna 3: Akcje i odesłanie do mapy -->
            <td class="p-3.5 sm:p-4 align-top text-right w-2/12">
              ${item.is_active ? `
                <a 
                  href="index.html?street=${item.geojson_id}" 
                  class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-600 hover:text-white border border-blue-200 transition-all shadow-xs"
                  title="Zobacz tę ulicę na mapie Krakowa"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  </svg>
                  <span>Mapa</span>
                </a>
              ` : `
                <span class="text-xs text-slate-400 italic">archiwalna</span>
              `}
            </td>
          </tr>
        `;
      });

      html += `
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    tableContainer.innerHTML = html;
  }

  renderDebates() {
    const container = document.getElementById('debates-content-area');
    if (!container || !this.data || !this.data.debates) return;

    let html = `
      <div class="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs max-w-4xl mx-auto space-y-6">
        <div class="text-center pb-4 border-b border-slate-100">
          <span class="text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-100">
            Stenogram sesji Rady Miasta Krakowa
          </span>
          <h3 class="text-xl font-bold text-slate-900 mt-2">
            Posiedzenie z 17 lipca 1912 r. (kadencja XVI, sesja 32)
          </h3>
          <p class="text-xs text-slate-500 mt-1">
            Rocznik XXXIII, Nr 8, str. 155–156 • Przewodniczący: dr Juliusz Leo
          </p>
        </div>

        <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs sm:text-sm text-slate-700 leading-relaxed space-y-2">
          <p>
            <strong>Przebieg posiedzenia:</strong> Referent Sekcyi I radca budownictwa Górecki przedłożył całościowy projekt nazewnictwa dla przyłączonych dzielnic.
            Wiceprezydent <strong>dr Henryk Szarski</strong> uzasadniał pilność uchwały: 
            <em class="text-slate-900 font-medium">„Wszyscy się skarżą, że poczta listów nie doręcza, bo brak adresów dokładnych na przyłączonych terenach.”</em>
          </p>
        </div>

        <div class="space-y-4">
    `;

    this.data.debates.forEach(d => {
      html += `
        <div class="p-5 rounded-xl bg-slate-50/70 border border-slate-200 hover:border-slate-300 transition-colors">
          <div class="flex items-center justify-between text-xs font-semibold mb-1.5">
            <span class="text-blue-700 uppercase font-bold tracking-wider">${d.district}</span>
            <span class="text-slate-500 font-mono text-[11px]">DRK s. ${d.page_printed}</span>
          </div>
          <h4 class="text-base font-bold text-slate-900 mb-1.5">
            ${d.topic}
          </h4>
          <div class="text-xs text-slate-600 mb-2">
            <strong>Głos w dyskusji:</strong> <span class="font-medium text-slate-800">${d.speaker}</span>
          </div>
          <p class="text-xs sm:text-sm text-slate-700 leading-relaxed">
            ${d.summary}
          </p>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  filterTable() {
    const q = this.searchQuery;
    let visibleCount = 0;

    document.querySelectorAll('.parallel-row').forEach(row => {
      const text = row.dataset.searchText || '';
      const matches = !q || text.includes(q);
      row.style.display = matches ? '' : 'none';
      if (matches) visibleCount++;
    });

    // Ukryj nagłówki dzielnic jeśli puste
    document.querySelectorAll('.district-block').forEach(block => {
      const hasVisible = Array.from(block.querySelectorAll('.parallel-row')).some(r => r.style.display !== 'none');
      block.style.display = hasVisible ? '' : 'none';
    });

    const countEl = document.getElementById('search-matches-count');
    if (countEl) {
      countEl.textContent = q ? `Znaleziono: ${visibleCount} ulic` : '';
    }
  }

  handleInitialHash() {
    let hash = window.location.hash.replace('#', '').trim();
    if (!hash || hash === 'all') return;

    // Przełącz widok na tabelę
    if (this.activeView !== 'table') {
      this.switchView('table');
    }

    // Spróbuj znaleźć wiersz o id = hash lub data-geojson-id = hash
    let row = document.getElementById(hash);
    if (!row) {
      row = document.querySelector(`[data-geojson-id="${hash}"]`);
    }

    if (row) {
      setTimeout(() => {
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        row.classList.add('row-highlight');
      }, 250);
    }
  }
}

// Globalna instancja
window.drkPage = new DrkArchivePage();
