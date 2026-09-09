/**
 * Główna logika aplikacji Ulice Krakowa: MapLibre GL JS, warstwy, podświetlenie, interakcje
 */

// Style wektorowe z CARTO (darmowe, bez klucza API, oparte na wektorach i WebGL)
const MAP_STYLES = {
  positron: {
    name: 'Minimalny Jasny (Positron)',
    url: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
  },
  dark: {
    name: 'Ciemny / Neon (Dark Matter)',
    url: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
  },
  voyager: {
    name: 'Klasyczny Kolorowy (Voyager)',
    url: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json'
  }
};

class KrakowStreetsApp {
  constructor() {
    this.currentStyle = 'positron';
    this.streetsData = null;
    this.borderData = null;
    this.showBorder = true;
    this.selectedStreetId = null;
    this.search = null;

    this.init();
  }

  async init() {
    // Koordynaty centrum Krakowa (Rynek Główny)
    this.map = new maplibregl.Map({
      container: 'map',
      style: MAP_STYLES[this.currentStyle].url,
      center: [19.944979, 50.061650],
      zoom: 13,
      pitch: 30, // Lekkie nachylenie 3D
      bearing: 0,
      attributionControl: true
    });

    // Kontrolki nawigacji (zoom, rotacja 3D)
    this.map.addControl(new maplibregl.NavigationControl({
      visualizePitch: true
    }), 'top-right');

    this.initUIEvents();

    // Funkcja pomocnicza: bezpieczne dodanie warstw po gotowości danych i stylu
    const trySetupLayers = () => {
      if (!this.streetsData) return;
      this.setupMapLayers();
      if (this.selectedStreetId) {
        this.updateSelectionLayers();
      }
    };

    // Rejestracja nasłuchiwania na zdarzenia ładowania stylów
    this.map.on('style.load', trySetupLayers);
    this.map.on('load', trySetupLayers);

    // Globalna obsługa kliknięcia w ulicę na mapie (nie ginie przy podmianie stylu)
    this.map.on('click', (e) => {
      if (!this.map.getLayer('streets-base')) return;
      const features = this.map.queryRenderedFeatures(e.point, { layers: ['streets-base'] });
      if (features && features.length > 0) {
        const featureId = features[0].properties.id;
        const street = this.streetsData?.features.find(f => f.properties.id === featureId);
        if (street) {
          this.selectStreet(street);
        }
      }
    });

    // Zmiana kursora nad ulicami
    this.map.on('mousemove', (e) => {
      if (!this.map.getLayer('streets-base')) {
        this.map.getCanvas().style.cursor = '';
        return;
      }
      const features = this.map.queryRenderedFeatures(e.point, { layers: ['streets-base'] });
      this.map.getCanvas().style.cursor = features.length > 0 ? 'pointer' : '';
    });

    // Pobranie danych GeoJSON (ulice oraz granice administracyjne Krakowa)
    try {
      const [streetsResp, borderResp] = await Promise.all([
        fetch('data/krakow_streets.geojson').catch(() => fetch('data/streets_sample.json')),
        fetch('data/krakow_border.geojson').catch(() => null)
      ]);

      if (streetsResp && streetsResp.ok) {
        this.streetsData = await streetsResp.json();
      } else {
        const fallback = await fetch('data/streets_sample.json');
        this.streetsData = await fallback.json();
      }

      if (borderResp && borderResp.ok) {
        this.borderData = await borderResp.json();
      }

      this.initSearch();
      this.updateTotalStreetsCount();
      trySetupLayers();
    } catch (err) {
      try {
        const resp = await fetch('data/streets_sample.json');
        this.streetsData = await resp.json();
        this.initSearch();
        this.updateTotalStreetsCount();
        trySetupLayers();
      } catch (innerErr) {
        console.error('Błąd ładowania danych ulic:', innerErr);
      }
    }
  }

  setupMapLayers() {
    if (!this.streetsData) return;

    try {
      const isDark = this.currentStyle === 'dark';

      // 0. Warstwa granic administracyjnych Krakowa (czerwona obwódka i subtelny obrys)
      if (this.borderData) {
        if (!this.map.getSource('krakow-border')) {
          this.map.addSource('krakow-border', {
            type: 'geojson',
            data: this.borderData
          });
        }

        if (!this.map.getLayer('krakow-border-fill')) {
          this.map.addLayer({
            id: 'krakow-border-fill',
            type: 'fill',
            source: 'krakow-border',
            layout: {
              visibility: this.showBorder ? 'visible' : 'none'
            },
            paint: {
              'fill-color': isDark ? '#38bdf8' : '#2563eb',
              'fill-opacity': isDark ? 0.03 : 0.015
            }
          });
        }

        if (!this.map.getLayer('krakow-border-glow')) {
          this.map.addLayer({
            id: 'krakow-border-glow',
            type: 'line',
            source: 'krakow-border',
            layout: {
              'line-join': 'round',
              'line-cap': 'round',
              visibility: this.showBorder ? 'visible' : 'none'
            },
            paint: {
              'line-color': isDark ? '#fb7185' : '#ef4444',
              'line-width': 6,
              'line-blur': 4,
              'line-opacity': 0.35
            }
          });
        }

        if (!this.map.getLayer('krakow-border-line')) {
          this.map.addLayer({
            id: 'krakow-border-line',
            type: 'line',
            source: 'krakow-border',
            layout: {
              'line-join': 'round',
              'line-cap': 'round',
              visibility: this.showBorder ? 'visible' : 'none'
            },
            paint: {
              'line-color': isDark ? '#f43f5e' : '#dc2626',
              'line-width': 2.5,
              'line-dasharray': [4, 3],
              'line-opacity': 0.95
            }
          });
        }
      }

      // 1. Dodanie źródła danych GeoJSON dla ulic
      if (!this.map.getSource('krakow-streets')) {
        this.map.addSource('krakow-streets', {
          type: 'geojson',
          data: this.streetsData
        });
      }

      const baseColor = isDark ? '#60a5fa' : '#2563eb';

      // 2. Warstwa bazowa wszystkich ulic w bazie
      if (!this.map.getLayer('streets-base')) {
        this.map.addLayer({
          id: 'streets-base',
          type: 'line',
          source: 'krakow-streets',
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': baseColor,
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              11, 2.5,
              14, 4.5,
              17, 7.5
            ],
            'line-opacity': isDark ? 0.75 : 0.55
          }
        });
      }

      // 3. Warstwa poświaty (Glow / Halo) dla wybranej ulicy
      if (!this.map.getLayer('streets-selected-glow')) {
        this.map.addLayer({
          id: 'streets-selected-glow',
          type: 'line',
          source: 'krakow-streets',
          filter: ['==', ['get', 'id'], this.selectedStreetId || ''],
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': isDark ? '#38bdf8' : '#2563eb',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              11, 10,
              14, 16,
              17, 26
            ],
            'line-blur': [
              'interpolate', ['linear'], ['zoom'],
              11, 5,
              14, 8,
              17, 14
            ],
            'line-opacity': 0.85
          }
        });
      }

      // 4. Warstwa ostrej, nasyconej linii wybranej ulicy
      if (!this.map.getLayer('streets-selected-line')) {
        this.map.addLayer({
          id: 'streets-selected-line',
          type: 'line',
          source: 'krakow-streets',
          filter: ['==', ['get', 'id'], this.selectedStreetId || ''],
          layout: {
            'line-join': 'round',
            'line-cap': 'round'
          },
          paint: {
            'line-color': isDark ? '#bae6fd' : '#1d4ed8',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              11, 4,
              14, 6,
              17, 9.5
            ],
            'line-opacity': 1.0
          }
        });
      }
    } catch (err) {
      console.warn('Oczekiwanie na pełne załadowanie arkusza stylu...', err);
    }
  }

  updateSelectionLayers() {
    const id = this.selectedStreetId || '';
    if (this.map.getLayer('streets-selected-glow')) {
      this.map.setFilter('streets-selected-glow', ['==', ['get', 'id'], id]);
    }
    if (this.map.getLayer('streets-selected-line')) {
      this.map.setFilter('streets-selected-line', ['==', ['get', 'id'], id]);
    }
  }

  initSearch() {
    this.search = new StreetSearch(this.streetsData.features, (street) => {
      this.selectStreet(street);
    });
  }

  selectStreetById(id) {
    if (!this.streetsData) return;
    const street = this.streetsData.features.find(f => f.properties.id === id);
    if (street) {
      this.selectStreet(street);
    }
  }

  selectStreet(street) {
    this.selectedStreetId = street.properties.id;
    this.updateSelectionLayers();

    // Obliczenie granic geometrii (Bounding Box)
    const bounds = new maplibregl.LngLatBounds();
    const geom = street.geometry;

    if (geom.type === 'LineString') {
      geom.coordinates.forEach(coord => bounds.extend(coord));
    } else if (geom.type === 'MultiLineString') {
      geom.coordinates.forEach(line => {
        line.forEach(coord => bounds.extend(coord));
      });
    }

    // Płynny przelot kamery do ulicy z nachyleniem 3D i odsunięciem dla panelu bocznego
    const isMobile = window.innerWidth < 768;
    this.map.fitBounds(bounds, {
      padding: isMobile 
        ? { top: 120, bottom: 320, left: 30, right: 30 }
        : { top: 100, bottom: 80, left: 80, right: 460 },
      pitch: 42,
      bearing: 12,
      maxZoom: 16.5,
      duration: 1600,
      essential: true
    });

    // Wyświetlenie danych w bocznym panelu
    this.selectedStreetProps = street.properties;
    this.renderStreetDrawer(street.properties);
  }

  renderStreetDrawer(props) {
    if (!props) return;
    this.selectedStreetProps = props;

    const drawer = document.getElementById('street-drawer');
    const emptyState = document.getElementById('drawer-empty-state');
    const content = document.getElementById('drawer-content');

    emptyState.classList.add('hidden');
    content.classList.remove('hidden');

    const i18n = window.krakowI18n;
    const currentLang = i18n ? i18n.currentLang : 'pl';

    // 1. Nagłówek i podstawowe metryki
    const districtText = i18n ? i18n.localize(props.district, 'Kraków') : (props.district || 'Kraków');
    const categoryText = i18n ? i18n.localize(props.category, 'Ogólna') : (props.category || 'Ogólna');
    const rawName = i18n ? i18n.localize(props.name, '') : (props.name || '');
    const fullNameText = i18n ? i18n.localize(props.full_name, `ulica ${rawName}`) : (props.full_name || `ulica ${rawName}`);

    document.getElementById('drawer-district').textContent = districtText;
    document.getElementById('drawer-category').textContent = categoryText;
    document.getElementById('drawer-name').textContent = fullNameText;

    // Dosłowne znaczenie dla obcokrajowców (literal_meaning) - widoczne dla EN i DE lub gdy dostępne
    const meaningBox = document.getElementById('drawer-meaning-box');
    const meaningTextEl = document.getElementById('drawer-meaning-text');
    const literalMeaning = props.literal_meaning ? (i18n ? i18n.localize(props.literal_meaning) : null) : null;

    if (meaningBox && meaningTextEl) {
      if (literalMeaning && currentLang !== 'pl') {
        meaningTextEl.textContent = `„${literalMeaning}”`;
        meaningBox.classList.remove('hidden');
      } else {
        meaningBox.classList.add('hidden');
      }
    }

    const yearPrefix = i18n ? i18n.t('metric_label') : 'Początki:';
    const fallbackPeriod = currentLang === 'pl' ? 'Średniowiecze' : (currentLang === 'de' ? 'Mittelalter' : 'Middle Ages');
    document.getElementById('drawer-year').textContent = props.year ? `${yearPrefix} ${props.year}` : fallbackPeriod;
    document.getElementById('drawer-length').textContent = props.length_meters ? `${props.length_meters} m` : '—';

    // 2. Karta Patrona Ulicy (tylko dla ulic z patronem osobowym)
    const patronCard = document.getElementById('drawer-patron-card');
    const patron = props.patron;

    if (patron && patron.name) {
      document.getElementById('drawer-patron-name').textContent = patron.name;
      const patronRoleText = i18n ? i18n.localize(patron.role, '') : (patron.role || '');
      document.getElementById('drawer-patron-role').textContent = patronRoleText;
      
      const patronImg = document.getElementById('drawer-patron-img');
      if (patron.image) {
        patronImg.src = patron.image;
        patronImg.alt = patron.name;
        patronImg.onerror = () => { patronImg.classList.add('hidden'); };
        patronImg.classList.remove('hidden');
      } else {
        patronImg.classList.add('hidden');
      }

      const wikiBtn = document.getElementById('drawer-patron-wiki');
      const wikiUrl = patron.wiki_url || patron.wikipedia_url;
      if (wikiUrl) {
        wikiBtn.href = wikiUrl;
        wikiBtn.classList.remove('hidden');
      } else {
        wikiBtn.classList.add('hidden');
      }

      patronCard.classList.remove('hidden');
    } else {
      patronCard.classList.add('hidden');
    }

    // 3. Etymologia i historia nazwy z obsługą i18n
    const etymologyEl = document.getElementById('drawer-etymology');
    const etymologyText = i18n ? i18n.localize(props.etymology, '') : (props.etymology || '');
    const sourceLabel = i18n ? i18n.t('source_label') : 'Źródło:';
    const openDocLabel = i18n ? i18n.t('open_doc') : 'Otwórz dokument';

    const source = props.source || {
      name: props.resolution?.has_resolution 
        ? 'Rada Miasta Krakowa / BIP Kraków' 
        : 'E. Supranowicz, „Nazwy ulic Krakowa” (IJP PAN, 1995, ISBN 83-85579-48-6)',
      url: null,
      label: null
    };

    etymologyEl.innerHTML = `
      <p class="leading-relaxed text-slate-700">${etymologyText}</p>
      <div class="mt-3.5 pt-3 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500">
        <span class="flex items-center gap-1.5 text-slate-600 font-medium">
          <svg class="w-3.5 h-3.5 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
          </svg>
          <span>${sourceLabel} ${source.name}</span>
        </span>
        ${source.url ? `
        <a href="${source.url}" target="_blank" rel="noopener noreferrer" class="font-semibold text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-0.5">
          <span>${source.label || openDocLabel}</span>
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
          </svg>
        </a>` : ''}
      </div>
    `;

    // 4. Karta uchwały RMK (akty prawa miejscowego z BIP)
    const res = props.resolution;
    const resBox = document.getElementById('drawer-resolution-box');

    if (res && res.has_resolution) {
      resBox.classList.remove('hidden');
      resBox.className = 'mt-5 p-4 rounded-xl border border-blue-200 bg-blue-50/60 shadow-sm transition-all';
      
      const resTitle = i18n ? i18n.t('resolution_title') : 'Akt Prawa Miejscowego (RMK)';
      const drukLabel = res.druk_number ? (i18n ? i18n.t('druk_sublabel', res.druk_number) : `${res.druk_number}: projekt z oficjalnym uzasadnieniem`) : '';
      const openDrukText = i18n ? i18n.t('open_druk_pdf') : 'Otwórz Druk RMK z Uzasadnieniem (PDF)';
      const viewResBipText = i18n ? i18n.t('view_resolution_bip') : 'Uchwała w BIP';
      const downloadResPdfText = i18n ? i18n.t('download_resolution_pdf') : 'Uchwała (PDF)';
      const viewLegPathText = i18n ? i18n.t('view_leg_path') : 'Zobacz ścieżkę legislacyjną i druki w BIP &rarr;';

      resBox.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <span class="inline-flex items-center gap-1.5 text-xs font-bold text-blue-800 uppercase tracking-wider">
            <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            ${resTitle}
          </span>
          <span class="text-xs text-blue-600 font-semibold">${res.date || ''}</span>
        </div>
        <h4 class="font-bold text-slate-900 text-sm mb-0.5">${res.number}</h4>
        ${res.druk_number ? `
        <div class="text-[11px] font-semibold text-blue-700 mb-2 flex items-center gap-1.5 bg-blue-100/60 px-2 py-1 rounded-md">
          <svg class="w-3.5 h-3.5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>${drukLabel}</span>
        </div>` : ''}
        <p class="text-xs text-slate-600 mb-3 italic leading-relaxed">„${res.official_basis || ''}”</p>
        
        <div class="space-y-2 pt-1">
          ${res.druk_pdf_url ? `
          <a href="${res.druk_pdf_url}" target="_blank" rel="noopener noreferrer" 
             class="inline-flex items-center justify-center w-full gap-2 px-3 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <span>${openDrukText}</span>
          </a>` : ''}

          <div class="grid grid-cols-2 gap-2">
            <a href="${res.bip_url}" target="_blank" rel="noopener noreferrer" 
               class="inline-flex items-center justify-center gap-1 px-2.5 py-1.5 text-[11px] font-semibold text-blue-700 bg-blue-100/80 hover:bg-blue-200 rounded-lg transition-colors border border-blue-200 text-center">
              <span>${viewResBipText}</span>
              <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
              </svg>
            </a>

            ${res.pdf_url ? `
            <a href="${res.pdf_url}" target="_blank" rel="noopener noreferrer" 
               class="inline-flex items-center justify-center gap-1 px-2.5 py-1.5 text-[11px] font-semibold text-blue-700 bg-blue-100/80 hover:bg-blue-200 rounded-lg transition-colors border border-blue-200 text-center">
              <span>${downloadResPdfText}</span>
              <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </a>` : ''}
          </div>

          ${res.druk_url ? `
          <div class="text-center pt-1">
            <a href="${res.druk_url}" target="_blank" rel="noopener noreferrer" class="text-[11px] text-blue-600 hover:underline inline-flex items-center gap-1">
              <span>${viewLegPathText}</span>
            </a>
          </div>` : ''}
        </div>
      `;
    } else {
      resBox.innerHTML = '';
      resBox.className = 'hidden';
    }

    // Otwórz szufladę jeśli była schowana (na mobile)
    drawer.classList.remove('translate-y-full', 'md:translate-x-full');
  }

  initUIEvents() {
    // Inicjalizacja stanu i18n
    if (window.krakowI18n) {
      window.krakowI18n.updateDOM();
    }

    // Nasłuchiwanie na zmianę języka
    window.addEventListener('languagechange', () => {
      this.updateTotalStreetsCount();
      if (this.selectedStreetProps) {
        this.renderStreetDrawer(this.selectedStreetProps);
      }
    });

    // Przełącznik stylu mapy (Positron / Dark Matter / Voyager)
    const styleSelect = document.getElementById('map-style-select');
    if (styleSelect) {
      styleSelect.addEventListener('change', (e) => {
        this.currentStyle = e.target.value;
        const styleUrl = MAP_STYLES[this.currentStyle].url;

        // Ustawienie nowego stylu – 'style.load' automatycznie odbuduje warstwy i przywróci selekcję
        this.map.setStyle(styleUrl);
      });
    }

    // Zamknięcie szuflady
    const closeBtn = document.getElementById('close-drawer-btn');
    const drawer = document.getElementById('street-drawer');
    if (closeBtn && drawer) {
      closeBtn.addEventListener('click', () => {
        drawer.classList.add('translate-y-full', 'md:translate-x-full');
        this.selectedStreetId = null;
        this.selectedStreetProps = null;
        this.updateSelectionLayers();
      });
    }

    // Przełącznik widoczności granic Krakowa
    const toggleBorderBtn = document.getElementById('toggle-border-btn');
    if (toggleBorderBtn) {
      toggleBorderBtn.addEventListener('click', () => {
        this.toggleBorder();
      });
    }

    // Przycisk dopasowania widoku do całego Krakowa
    const fitBoundsBtn = document.getElementById('fit-bounds-btn');
    if (fitBoundsBtn) {
      fitBoundsBtn.addEventListener('click', () => {
        this.fitKrakowBounds();
      });
    }
  }

  toggleBorder() {
    this.showBorder = !this.showBorder;
    const visibility = this.showBorder ? 'visible' : 'none';
    ['krakow-border-fill', 'krakow-border-glow', 'krakow-border-line'].forEach(layerId => {
      if (this.map.getLayer(layerId)) {
        this.map.setLayoutProperty(layerId, 'visibility', visibility);
      }
    });

    const toggleBtn = document.getElementById('toggle-border-btn');
    const indicatorDot = document.getElementById('border-indicator-dot');
    if (toggleBtn) {
      if (this.showBorder) {
        toggleBtn.classList.add('text-red-600');
        toggleBtn.classList.remove('text-slate-400');
        if (indicatorDot) {
          indicatorDot.className = 'w-2.5 h-2.5 rounded-full bg-red-600 shadow-sm animate-pulse';
        }
      } else {
        toggleBtn.classList.remove('text-red-600');
        toggleBtn.classList.add('text-slate-400');
        if (indicatorDot) {
          indicatorDot.className = 'w-2.5 h-2.5 rounded-full bg-slate-300';
        }
      }
    }
  }

  fitKrakowBounds() {
    // Oficjalny BBox Krakowa: [19.7922, 49.9676] - [20.2173, 50.1261]
    const bounds = [
      [19.7922, 49.9676],
      [20.2173, 50.1261]
    ];
    this.map.fitBounds(bounds, {
      padding: { top: 70, bottom: 60, left: 60, right: 60 },
      pitch: 0,
      bearing: 0,
      duration: 1400,
      essential: true
    });
  }

  updateTotalStreetsCount() {
    const counterEl = document.getElementById('streets-count-badge');
    if (counterEl && this.streetsData) {
      const count = this.streetsData.features.length;
      counterEl.textContent = window.krakowI18n ? window.krakowI18n.t('streets_count', count) : `${count} ulic w bazie`;
    }
  }
}

// Inicjalizacja po załadowaniu DOM
document.addEventListener('DOMContentLoaded', () => {
  window.krakowApp = new KrakowStreetsApp();
});
