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
    this.districtsData = null;
    this.showDistricts = false;
    this.expansionsData = null;
    this.showExpansionTimeline = false;
    this.currentExpansionIndex = 1; // Domyślnie Wielki Kraków 1910-1915

    this.init();
  }

  async init() {
    // Ograniczenie obszaru mapy – zapobiega oddaleniu do mapy świata i ucieczce z Krakowa
    const KRAKOW_BOUNDS = [
      [19.65, 49.88], // Południowy zachód
      [20.35, 50.22]  // Północny wschód
    ];

    // Koordynaty centrum Krakowa (Rynek Główny)
    this.map = new maplibregl.Map({
      container: 'map',
      style: MAP_STYLES[this.currentStyle].url,
      center: [19.944979, 50.061650],
      zoom: 13,
      minZoom: 10.4, // Blokada zbytniego oddalenia
      maxZoom: 19,
      maxBounds: KRAKOW_BOUNDS,
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
      if (!this.streetsData || !this.map || !this.styleReady) return;
      this.setupMapLayers();
      if (this.selectedStreetId) {
        this.updateSelectionLayers();
      }
      this.updateDistrictsLayers();
      this.updateExpansionHighlight();
    };

    // Odbuduj nakładki raz po załadowaniu stylu, niezależnie od ładowania źródeł.
    this.map.on('style.load', () => {
      this.styleReady = true;
      trySetupLayers();
    });

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

    // Pobranie danych GeoJSON (ulice, granice, dzielnice, rozwój terytorialny)
    try {
      const [streetsResp, borderResp, districtsResp, expansionsResp] = await Promise.all([
        fetch('data/krakow_streets.geojson').catch(() => fetch('data/streets_sample.json')),
        fetch('data/krakow_border.geojson').catch(() => null),
        fetch('data/krakow_districts.geojson').catch(() => null),
        fetch('data/krakow_expansions.json').catch(() => null)
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
      if (districtsResp && districtsResp.ok) {
        this.districtsData = await districtsResp.json();
      }
      if (expansionsResp && expansionsResp.ok) {
        this.expansionsData = await expansionsResp.json();
      }

      this.initSearch();
      this.initExpansionMilestones();
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

      // 0.5. Warstwa 18 dzielnic Krakowa oraz rozwoju terytorialnego
      if (this.districtsData) {
        if (!this.map.getSource('krakow-districts')) {
          this.map.addSource('krakow-districts', {
            type: 'geojson',
            data: this.districtsData
          });
        }

        if (!this.map.getLayer('districts-fill')) {
          this.map.addLayer({
            id: 'districts-fill',
            type: 'fill',
            source: 'krakow-districts',
            layout: {
              visibility: (this.showDistricts || this.showExpansionTimeline) ? 'visible' : 'none'
            },
            paint: {
              'fill-color': isDark ? '#f43f5e' : '#dc2626',
              'fill-opacity': isDark ? 0.05 : 0.03
            }
          });
        }

        if (!this.map.getLayer('districts-line')) {
          this.map.addLayer({
            id: 'districts-line',
            type: 'line',
            source: 'krakow-districts',
            layout: {
              'line-join': 'round',
              'line-cap': 'round',
              visibility: (this.showDistricts || this.showExpansionTimeline) ? 'visible' : 'none'
            },
            paint: {
              'line-color': isDark ? '#f43f5e' : '#dc2626',
              'line-width': 2,
              'line-dasharray': [3, 2],
              'line-opacity': 0.85
            }
          });
        }

        // Warstwa podświetlenia terytorium dla wybranego etapu rozwoju
        if (!this.map.getLayer('districts-expansion-fill')) {
          this.map.addLayer({
            id: 'districts-expansion-fill',
            type: 'fill',
            source: 'krakow-districts',
            layout: {
              visibility: this.showExpansionTimeline ? 'visible' : 'none'
            },
            paint: {
              'fill-color': isDark ? '#fbbf24' : '#f59e0b',
              'fill-opacity': isDark ? 0.22 : 0.16
            }
          });
        }

        if (!this.map.getLayer('districts-expansion-line')) {
          this.map.addLayer({
            id: 'districts-expansion-line',
            type: 'line',
            source: 'krakow-districts',
            layout: {
              'line-join': 'round',
              'line-cap': 'round',
              visibility: this.showExpansionTimeline ? 'visible' : 'none'
            },
            paint: {
              'line-color': isDark ? '#f59e0b' : '#d97706',
              'line-width': 2.2,
              'line-opacity': 0.85
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
            'line-opacity': (isDark ? 0.75 : 0.55) * ((this.showDistricts || this.showExpansionTimeline) ? 0.8 : 1)
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

      // Wielojęzyczny link do Wikipedii (PL / EN / DE)
      const wikiBtn = document.getElementById('drawer-patron-wiki');
      let wikiUrl = null;
      if (patron.wiki_urls && typeof patron.wiki_urls === 'object') {
        wikiUrl = patron.wiki_urls[currentLang] || patron.wiki_urls['pl'];
      }
      if (!wikiUrl) {
        wikiUrl = patron.wiki_url || patron.wikipedia_url;
      }

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

    // 3. Etymologia oraz zintegrowana OŚ CZASU ZMIAN NAZWY
    const etymologyEl = document.getElementById('drawer-etymology');
    const etymologyText = i18n ? i18n.localize(props.etymology, '') : (props.etymology || '');
    
    // Zbieranie chronologii historycznych zmian nazwy (oś czasu)
    const timelineEvents = [];

    // 1880
    if (props.drk_1880 && props.drk_1880.official_name) {
      timelineEvents.push({
        year: 1880,
        badge: currentLang === 'pl' ? 'Regulacja 1880' : (currentLang === 'de' ? 'Regulierung 1880' : 'Regulation 1880'),
        desc: currentLang === 'pl'
          ? `Dawne miano: <em>„${props.drk_1880.former_description}”</em> &rarr; uregulowano: <strong>${props.drk_1880.official_name}</strong>`
          : (currentLang === 'de'
            ? `Früher: <em>„${props.drk_1880.former_description}”</em> &rarr; <strong>${props.drk_1880.official_name}</strong>`
            : `Former name: <em>„${props.drk_1880.former_description}”</em> &rarr; <strong>${props.drk_1880.official_name}</strong>`)
      });
    }

    // 1912
    if (props.drk_1912 && props.drk_1912.official_name) {
      timelineEvents.push({
        year: 1912,
        badge: currentLang === 'pl' ? 'Wielki Kraków' : (currentLang === 'de' ? 'Groß-Krakau' : 'Greater Kraków'),
        desc: currentLang === 'pl'
          ? `Uchwalono: <strong>${props.drk_1912.official_name}</strong> (dawniej <em>„${props.drk_1912.former_description}”</em>)`
          : (currentLang === 'de'
            ? `Beschlossen als <strong>${props.drk_1912.official_name}</strong> (früher <em>„${props.drk_1912.former_description}”</em>)`
            : `Enacted as <strong>${props.drk_1912.official_name}</strong> (formerly <em>„${props.drk_1912.former_description}”</em>)`)
      });
    }

    // 1917
    if (props.podgorze_1917 && props.podgorze_1917.official_name) {
      timelineEvents.push({
        year: 1917,
        badge: currentLang === 'pl' ? 'Unifikacja Podgórza' : (currentLang === 'de' ? 'Podgórze-Vereinigung' : 'Podgórze Unification'),
        desc: currentLang === 'pl'
          ? `Zniesiono zdublowane miano: <em>„${props.podgorze_1917.former_description}”</em> &rarr; <strong>${props.podgorze_1917.official_name}</strong>`
          : (currentLang === 'de'
            ? `Doppelter Name ersetzt: <em>„${props.podgorze_1917.former_description}”</em> &rarr; <strong>${props.podgorze_1917.official_name}</strong>`
            : `Replaced duplicate name: <em>„${props.podgorze_1917.former_description}”</em> &rarr; <strong>${props.podgorze_1917.official_name}</strong>`)
      });
    }

    // 1926
    if (props.drk_1926_1933 && props.drk_1926_1933.official_name) {
      timelineEvents.push({
        year: props.drk_1926_1933.year || 1926,
        badge: currentLang === 'pl' ? 'Modernizm II RP' : (currentLang === 'de' ? 'Moderne II. RP' : 'Interwar Era'),
        desc: currentLang === 'pl'
          ? `Wytyczono/uregulowano: <strong>${props.drk_1926_1933.official_name}</strong> (${props.drk_1926_1933.former_description})`
          : (currentLang === 'de'
            ? `Trassiert/Reguliert: <strong>${props.drk_1926_1933.official_name}</strong> (${props.drk_1926_1933.former_description})`
            : `Laid out/regulated: <strong>${props.drk_1926_1933.official_name}</strong> (${props.drk_1926_1933.former_description})`)
      });
    }

    // 1940
    if (props.okupacja_1940_1941 && props.okupacja_1940_1941.official_name) {
      const prevDesc = props.okupacja_1940_1941.former_description ? ` (przed 1940: <em>„${props.okupacja_1940_1941.former_description}”</em>)` : '';
      const prevDescDe = props.okupacja_1940_1941.former_description ? ` (vor 1940: <em>„${props.okupacja_1940_1941.former_description}”</em>)` : '';
      const prevDescEn = props.okupacja_1940_1941.former_description ? ` (prior to 1940: <em>„${props.okupacja_1940_1941.former_description}”</em>)` : '';
      timelineEvents.push({
        year: 1940,
        badge: currentLang === 'pl' ? 'Okupacja Niemiecka' : (currentLang === 'de' ? 'Deutsche Besatzung' : 'German Occupation'),
        desc: currentLang === 'pl'
          ? `Zniemczono urzędowo na: <strong class="text-red-700">„${props.okupacja_1940_1941.official_name}”</strong>${prevDesc}`
          : (currentLang === 'de'
            ? `Amtlich umbenannt in: <strong class="text-red-700">„${props.okupacja_1940_1941.official_name}”</strong>${prevDescDe}`
            : `Germanized officially to: <strong class="text-red-700">„${props.okupacja_1940_1941.official_name}”</strong>${prevDescEn}`)
      });
    }

    // 1951
    if (props.prl_1951_1955 && props.prl_1951_1955.official_name) {
      const isNewStreet = (props.prl_1951_1955.former_description || '').toLowerCase().startsWith('now');
      const prevDesc = (!isNewStreet && props.prl_1951_1955.former_description) ? ` (wcześniej: <em>„${props.prl_1951_1955.former_description}”</em>)` : '';
      const prevDescDe = (!isNewStreet && props.prl_1951_1955.former_description) ? ` (vorher: <em>„${props.prl_1951_1955.former_description}”</em>)` : '';
      const prevDescEn = (!isNewStreet && props.prl_1951_1955.former_description) ? ` (formerly: <em>„${props.prl_1951_1955.former_description}”</em>)` : '';

      const plAction = isNewStreet ? 'Nowa nazwa epoki PRL' : 'Przemianowano w PRL na';
      const deAction = isNewStreet ? 'Neuer Name der VR Polen' : 'In der VR Polen umbenannt in';
      const enAction = isNewStreet ? 'PRL era new street name' : 'Renamed in PRL to';

      timelineEvents.push({
        year: 1951,
        badge: currentLang === 'pl' ? 'Okres PRL' : (currentLang === 'de' ? 'VR Polen' : 'PRL Era'),
        desc: currentLang === 'pl'
          ? `${plAction}: <strong class="text-purple-800">„${props.prl_1951_1955.official_name}”</strong>${prevDesc}`
          : (currentLang === 'de'
            ? `${deAction}: <strong class="text-purple-800">„${props.prl_1951_1955.official_name}”</strong>${prevDescDe}`
            : `${enAction}: <strong class="text-purple-800">„${props.prl_1951_1955.official_name}”</strong>${prevDescEn}`)
      });
    }

    // 1973
    if (props.rozszerzenie_1973_1975 && props.rozszerzenie_1973_1975.official_name) {
      timelineEvents.push({
        year: 1973,
        badge: currentLang === 'pl' ? 'Rozszerzenie Granic' : (currentLang === 'de' ? 'Stadterweiterung' : 'City Expansion'),
        desc: currentLang === 'pl'
          ? `Uchwalono jako: <strong>${props.rozszerzenie_1973_1975.official_name}</strong> (d. wiejska: <em>„${props.rozszerzenie_1973_1975.former_description}”</em>)`
          : (currentLang === 'de'
            ? `Eingemeindet als: <strong>${props.rozszerzenie_1973_1975.official_name}</strong> (Dorfname: <em>„${props.rozszerzenie_1973_1975.former_description}”</em>)`
            : `Incorporated as: <strong>${props.rozszerzenie_1973_1975.official_name}</strong> (former: <em>„${props.rozszerzenie_1973_1975.former_description}”</em>)`)
      });
    }

    // 1991
    if (props.dekomunizacja_1991 && props.dekomunizacja_1991.official_name) {
      timelineEvents.push({
        year: 1991,
        badge: currentLang === 'pl' ? 'Dekomunizacja' : (currentLang === 'de' ? 'Dekommunisierung' : 'Decommunization'),
        desc: currentLang === 'pl'
          ? `Usunięto patrona PRL: <em class="text-red-700">„${props.dekomunizacja_1991.former_description}”</em> &rarr; przywrócono tradycyjne miano`
          : (currentLang === 'de'
            ? `Kommunistischer Name entfernt: <em class="text-red-700">„${props.dekomunizacja_1991.former_description}”</em> &rarr; traditioneller Name wiederhergestellt`
            : `Removed communist name: <em class="text-red-700">„${props.dekomunizacja_1991.former_description}”</em> &rarr; restored historic name`)
      });
    }

    // Dodatkowe wydarzenia historyczne (z monografii Tomkowicza, Grabowskiego, Bąkowskiego)
    if (props.timeline && Array.isArray(props.timeline)) {
      props.timeline.forEach(ev => {
        if (ev && ev.year && ev.desc) {
          timelineEvents.push({
            year: ev.year,
            badge: ev.badge || (currentLang === 'pl' ? 'Monografia' : (currentLang === 'de' ? 'Monographie' : 'Monograph')),
            desc: ev.desc
          });
        }
      });
    }

    // Sortowanie chronologiczne osi czasu
    timelineEvents.sort((a, b) => a.year - b.year);

    let timelineHtml = '';
    if (timelineEvents.length > 0) {
      const timelineHeading = currentLang === 'pl' 
        ? 'Chronologia zmian nazw w źródłach:' 
        : (currentLang === 'de' ? 'Chronologie der Namensänderungen:' : 'Chronology of Name Changes:');

      timelineHtml = `
        <div class="mt-3.5 pt-3 border-t border-slate-200/70">
          <div class="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>${timelineHeading}</span>
          </div>
          <div class="relative pl-3.5 ml-1 border-l-2 border-blue-200 space-y-2">
            ${timelineEvents.map(ev => `
              <div class="relative text-xs">
                <span class="absolute -left-[1.2rem] top-1 w-2.5 h-2.5 rounded-full bg-blue-600 ring-4 ring-blue-50"></span>
                <div class="flex items-center gap-1.5 font-bold text-slate-900 leading-tight">
                  <span>${ev.year}</span>
                  <span class="text-[10px] font-semibold text-blue-800 bg-blue-50 border border-blue-200/60 px-1.5 py-0.2 rounded-md">
                    ${ev.badge}
                  </span>
                </div>
                <div class="text-[11px] text-slate-600 mt-0.5 leading-snug">
                  ${ev.desc}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    etymologyEl.innerHTML = `
      <p class="leading-relaxed text-slate-700">${etymologyText}</p>
      ${timelineHtml}
    `;

    // 4. Ukrycie starego boksu cyfrowego archiwum (żeby nie zaśmiecał draweru)
    const oldDrkBox = document.getElementById('drawer-drk-box');
    if (oldDrkBox) {
      oldDrkBox.classList.add('hidden');
      oldDrkBox.innerHTML = '';
    }

    // 5. Zintegrowana, subtelna sekcja "ŹRÓDŁA I CYFROWE ARCHIWUM" (rozwijana)
    const resBox = document.getElementById('drawer-resolution-box');
    if (resBox) {
      const res = props.resolution;
      const rawNumber = res?.number || res?.resolution_number || '';
      const resNumber = rawNumber ? (rawNumber.toLowerCase().startsWith('uchwała') ? rawNumber : `Uchwała Nr ${rawNumber}`) : '';
      const hasBip = res && res.has_resolution && resNumber;

      const sourceItems = [];

      // Źródło PAN / Supranowicz
      const hasSupranowicz = (props.source?.name && props.source.name.includes('Supranowicz')) || (!hasBip && props.year);
      if (hasSupranowicz) {
        sourceItems.push(`
          <div class="flex items-start justify-between gap-2 p-2 rounded-lg bg-white border border-slate-200/70 shadow-2xs">
            <div>
              <div class="font-bold text-slate-800 text-[11px]">
                prof. Elżbieta Supranowicz
              </div>
              <div class="text-[10px] text-slate-500 mt-0.5">
                „Nazwy ulic Krakowa”, Instytut Języka Polskiego PAN, Kraków 1995
              </div>
            </div>
            <a href="https://rcin.org.pl/dlibra/publication/43027/edition/24551" target="_blank" rel="noopener noreferrer" class="flex-shrink-0 text-[10px] font-bold text-blue-700 hover:text-blue-900 bg-blue-50 border border-blue-200 px-2 py-1 rounded-md no-underline">
              RCIN PAN &nearr;
            </a>
          </div>
        `);
      }

      // Źródło BIP RMK (uchwała)
      if (hasBip) {
        sourceItems.push(`
          <div class="flex items-start justify-between gap-2 p-2 rounded-lg bg-white border border-slate-200/70 shadow-2xs">
            <div>
              <div class="font-bold text-slate-800 text-[11px]">
                ${resNumber}
              </div>
              <div class="text-[10px] text-slate-500 mt-0.5">
                Akt Prawa Miejscowego RMK z dnia ${res.date || ''}
              </div>
            </div>
            ${res.url ? `
              <a href="${res.url}" target="_blank" rel="noopener noreferrer" class="flex-shrink-0 text-[10px] font-bold text-blue-700 hover:text-blue-900 bg-blue-50 border border-blue-200 px-2 py-1 rounded-md no-underline">
                BIP Kraków &nearr;
              </a>
            ` : ''}
          </div>
        `);
      }

      // Akty Cyfrowego Archiwum
      const actLinks = [
        { obj: props.drk_1880, doc: 'drk_1880', label: 'DRK 1880', full: 'Wielka Regulacja Autonomiczna' },
        { obj: props.drk_1912, doc: 'drk_1912', label: 'DRK 1912', full: 'Wielki Kraków' },
        { obj: props.podgorze_1917, doc: 'podgorze_1917', label: 'Podgórze 1917', full: 'Unifikacja Podgórza' },
        { obj: props.drk_1926_1933, doc: 'drk_1926_1933', label: 'DRK 1926–1933', full: 'Modernizm II RP' },
        { obj: props.okupacja_1940_1941, doc: 'okupacja_1940_1941', label: 'GG 1940', full: 'Okupacja Niemiecka' },
        { obj: props.prl_1951_1955, doc: 'prl_1951_1955', label: 'PRL 1951–1955', full: 'Nowa Huta i Stalinizacja' },
        { obj: props.rozszerzenie_1973_1975, doc: 'rozszerzenie_1973_1975', label: 'MRN 1973', full: 'Rozszerzenie Granic' },
        { obj: props.dekomunizacja_1991, doc: 'dekomunizacja_1991', label: 'RMK 1991', full: 'Wielka Dekomunizacja' }
      ];

      for (const al of actLinks) {
        if (al.obj && al.obj.official_name) {
          sourceItems.push(`
            <div class="flex items-center justify-between gap-2 p-2 rounded-lg bg-white border border-slate-200/70 shadow-2xs">
              <div class="min-w-0">
                <div class="font-bold text-slate-800 text-[11px] truncate">${al.label} • ${al.full}</div>
                <div class="text-[10px] text-slate-500 truncate">${al.obj.district_name || al.obj.district_id || ''}</div>
              </div>
              <a href="sources.html?doc=${al.doc}#${al.obj.ref_id || props.id}" target="_blank" rel="noopener noreferrer" class="flex-shrink-0 text-[10px] font-bold text-amber-800 hover:text-amber-950 bg-amber-50 border border-amber-200 px-2 py-1 rounded-md no-underline">
                Otwórz akt &nearr;
              </a>
            </div>
          `);
        }
      }

      // Jeśli mamy jakiekolwiek źródła, renderujemy subtelny panel rozwijany
      if (sourceItems.length > 0) {
        resBox.classList.remove('hidden');
        resBox.className = 'mt-3';

        const summaryLabel = currentLang === 'pl'
          ? `Źródła i akty urzędowe (${sourceItems.length})`
          : (currentLang === 'de' ? `Quellen und Rechtsakte (${sourceItems.length})` : `Sources & Municipal Acts (${sourceItems.length})`);
        const expandLabel = currentLang === 'pl' ? 'Szczegóły' : (currentLang === 'de' ? 'Details' : 'Details');

        resBox.innerHTML = `
          <details class="group rounded-xl border border-slate-200/80 bg-slate-50/70 hover:bg-slate-50 transition-all text-xs">
            <summary class="p-2.5 sm:p-3 flex items-center justify-between cursor-pointer select-none list-none">
              <div class="flex items-center gap-2 font-semibold text-slate-700 text-xs">
                <svg class="w-4 h-4 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                </svg>
                <span>${summaryLabel}</span>
              </div>
              <div class="flex items-center gap-1 text-slate-400 group-hover:text-slate-600 text-[11px] font-medium">
                <span>${expandLabel}</span>
                <svg class="w-3.5 h-3.5 transition-transform duration-200 group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </summary>
            <div class="px-3 pb-3 pt-1 border-t border-slate-200/60 space-y-2 mt-1">
              ${sourceItems.join('')}
            </div>
          </details>
        `;
      } else {
        resBox.classList.add('hidden');
        resBox.innerHTML = '';
      }
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
        this.styleReady = false;
        this.map.setStyle(styleUrl, { diff: false });
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

    // Przełącznik dzielnic Krakowa
    const toggleDistrictsBtn = document.getElementById('toggle-districts-btn');
    if (toggleDistrictsBtn) {
      toggleDistrictsBtn.addEventListener('click', () => {
        this.toggleDistricts();
      });
    }

    // Przełącznik osi rozwoju terytorialnego
    const toggleExpansionBtn = document.getElementById('toggle-expansion-btn');
    if (toggleExpansionBtn) {
      toggleExpansionBtn.addEventListener('click', () => {
        this.toggleExpansionTimeline();
      });
    }

    // Zamknięcie osi rozwoju terytorialnego
    const closeExpansionBtn = document.getElementById('close-expansion-btn');
    if (closeExpansionBtn) {
      closeExpansionBtn.addEventListener('click', () => {
        this.toggleExpansionTimeline(false);
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

  toggleDistricts() {
    this.showDistricts = !this.showDistricts;
    this.updateDistrictsLayers();

    const btn = document.getElementById('toggle-districts-btn');
    if (btn) {
      if (this.showDistricts) {
        btn.classList.add('text-red-600', 'font-bold');
        btn.classList.remove('text-slate-700');
      } else {
        btn.classList.remove('text-red-600', 'font-bold');
        btn.classList.add('text-slate-700');
      }
    }
  }

  updateDistrictsLayers() {
    if (!this.map) return;
    const shouldShow = this.showDistricts || this.showExpansionTimeline;
    if (this.map.getLayer('streets-base')) {
      this.map.setPaintProperty('streets-base', 'line-opacity', (this.currentStyle === 'dark' ? 0.75 : 0.55) * (shouldShow ? 0.8 : 1));
    }
    document.getElementById('toggle-districts-btn')?.setAttribute('aria-pressed', String(this.showDistricts));
    document.getElementById('toggle-expansion-btn')?.setAttribute('aria-pressed', String(this.showExpansionTimeline));
    const visibility = shouldShow ? 'visible' : 'none';

    ['districts-fill', 'districts-line'].forEach(id => {
      if (this.map.getLayer(id)) {
        this.map.setLayoutProperty(id, 'visibility', visibility);
      }
    });
  }

  toggleExpansionTimeline(forceState) {
    if (typeof forceState === 'boolean') {
      this.showExpansionTimeline = forceState;
    } else {
      this.showExpansionTimeline = !this.showExpansionTimeline;
    }

    const panel = document.getElementById('territory-expansion-panel');
    const btn = document.getElementById('toggle-expansion-btn');

    if (panel) {
      if (this.showExpansionTimeline) {
        panel.classList.remove('hidden');
        if (btn) {
          btn.classList.add('text-amber-600', 'font-bold');
          btn.classList.remove('text-slate-700');
        }
      } else {
        panel.classList.add('hidden');
        if (btn) {
          btn.classList.remove('text-amber-600', 'font-bold');
          btn.classList.add('text-slate-700');
        }
      }
    }

    this.updateDistrictsLayers();
    this.updateExpansionHighlight();
  }

  initExpansionMilestones() {
    const container = document.getElementById('expansion-milestones-container');
    if (!container || !this.expansionsData) return;

    container.innerHTML = this.expansionsData.map((stage, idx) => `
      <button onclick="window.krakowApp?.setExpansionStage(${idx})" data-stage-idx="${idx}" class="expansion-milestone-btn p-1.5 rounded-lg border text-center transition-all cursor-pointer ${idx === this.currentExpansionIndex ? 'bg-amber-600 text-white border-amber-700 shadow-xs font-bold' : 'bg-white/90 hover:bg-white text-slate-700 border-slate-200'}">
        <div class="text-[11px] font-bold leading-none">${stage.year}</div>
        <div class="text-[9px] opacity-80 mt-0.5 leading-none">${stage.area}</div>
      </button>
    `).join('');

    this.setExpansionStage(this.currentExpansionIndex);
  }

  setExpansionStage(index) {
    if (!this.expansionsData || !this.expansionsData[index]) return;
    this.currentExpansionIndex = index;
    const stage = this.expansionsData[index];

    const badge = document.getElementById('expansion-stage-badge');
    if (badge) {
      badge.textContent = `${stage.year} • ${stage.area}`;
    }

    const desc = document.getElementById('expansion-stage-desc');
    if (desc) {
      desc.innerHTML = `<span class="font-bold text-slate-800">${stage.title}:</span> ${stage.desc}`;
    }

    document.querySelectorAll('.expansion-milestone-btn').forEach(btn => {
      const idx = parseInt(btn.getAttribute('data-stage-idx'), 10);
      if (idx === index) {
        btn.className = 'expansion-milestone-btn p-1.5 rounded-lg border text-center transition-all cursor-pointer bg-amber-600 text-white border-amber-700 shadow-xs font-bold';
      } else {
        btn.className = 'expansion-milestone-btn p-1.5 rounded-lg border text-center transition-all cursor-pointer bg-white/90 hover:bg-white text-slate-700 border-slate-200';
      }
    });

    this.updateExpansionHighlight();
  }

  updateExpansionHighlight() {
    if (!this.map || !this.expansionsData) return;
    const visibility = this.showExpansionTimeline ? 'visible' : 'none';

    ['districts-expansion-fill', 'districts-expansion-line'].forEach(id => {
      if (this.map.getLayer(id)) {
        this.map.setLayoutProperty(id, 'visibility', visibility);
      }
    });

    if (this.showExpansionTimeline && this.expansionsData[this.currentExpansionIndex]) {
      const stage = this.expansionsData[this.currentExpansionIndex];
      const filter = ['in', ['get', 'id'], ['literal', stage.district_ids]];

      if (this.map.getLayer('districts-expansion-fill')) {
        this.map.setFilter('districts-expansion-fill', filter);
      }
      if (this.map.getLayer('districts-expansion-line')) {
        this.map.setFilter('districts-expansion-line', filter);
      }
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
