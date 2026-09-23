/**
 * Moduł wielojęzyczności (i18n) dla portalu Ulice Krakowa (PL / EN / DE)
 */

const UI_TRANSLATIONS = {
  pl: {
    locate_me: "Moja lokalizacja",
    location_unavailable: "Lokalizacja wymaga HTTPS lub localhost i obsługi w przeglądarce.",
    location_loading: "Baza ulic jeszcze się ładuje. Spróbuj za chwilę.",
    location_wait: "Ustalanie lokalizacji…",
    location_outside: "Nie znaleziono ulicy w pobliżu w krakowskiej bazie.",
    location_inaccurate: "Odczyt lokalizacji jest zbyt niedokładny. Spróbuj ponownie na zewnątrz.",
    location_denied: "Brak zgody na lokalizację. Możesz ją zmienić w ustawieniach przeglądarki.",
    location_timeout: "Upłynął czas ustalania lokalizacji. Spróbuj ponownie.",
    location_failed: "Nie udało się ustalić lokalizacji. Spróbuj ponownie.",
    location_found: (name, accuracy) => `Najbliższa ulica: ${name}. Dokładność lokalizacji: około ${accuracy} m.`,

    districts: "Dzielnice",
    streets_network: "Siatka ulic",
    streets_network_title: "Włącz / wyłącz widok pełnej siatki linii ulic",
    landmarks: "Miejsca i Osiedla",
    landmarks_title: "Włącz / wyłącz widok 151 osiedli, parków i mostów Krakowa",
    city_growth: "Rozwój 1910–Dziś",
    growth_title: "Rozwój terytorialny Krakowa",
    close_growth: "Zamknij oś rozwoju",

    search_placeholder: "Wyszukaj nazwę ulicy lub osiedla...",
    streets_count: (n) => `${n} ulic w bazie`,
    change_language: "Zmień język",
    map_style: "Styl mapy:",
    drawer_title: "Szczegóły Obiektu",
    empty_title: "Wybierz obiekt",
    empty_desc: "Wpisz nazwę w wyszukiwarce lub kliknij jedną z zaznaczonych linii bądź punktów na mapie.",
    patron_title: "Patron ulicy / obiektu",
    wiki_bio_link: "Zobacz biogram w Wikipedii",
    etymology_title: "Pochodzenie nazwy i etymologia",
    literal_meaning_label: "Dosłowne znaczenie:",
    source_label: "Źródło:",
    open_doc: "Otwórz dokument",
    resolution_title: "Akt Prawa Miejscowego (RMK)",
    druk_sublabel: (num) => `${num}: projekt z oficjalnym uzasadnieniem`,
    open_druk_pdf: "Otwórz Druk RMK z Uzasadnieniem (PDF)",
    view_resolution_bip: "Uchwała w BIP",
    download_resolution_pdf: "Uchwała (PDF)",
    view_leg_path: "Zobacz ścieżkę legislacyjną i druki w BIP →",
    no_results: "Nie znaleziono ulicy ani osiedla o podanej nazwie",
    resolution_badge: "Uchwała RMK",
    historical_badge: "Nazwa historyczna",
    metric_label: "Początki:",
    city_border: "Granice Krakowa",
    fit_krakow: "Całe miasto",
    footer_sources: "Źródła danych:",
    chip_wandy: "os. Wandy",
    chip_florianska: "ul. Floriańska",
    chip_szewska: "ul. Szewska",
    chip_kwiatowa: "ul. Kwiatowa",
    chip_szymborskiej: "Park Szymborskiej",
    chip_lema: "ul. Lema",
    chip_slowackiego: "al. Słowackiego",
    chip_dietla: "ul. Dietla",
    digital_archive_nav: "Cyfrowe Archiwum"
  },
  en: {
    locate_me: "My location",
    location_unavailable: "Location requires HTTPS or localhost and browser support.",
    location_loading: "Street data is still loading. Please try again shortly.",
    location_wait: "Finding your location…",
    location_outside: "No nearby street was found in the Kraków dataset.",
    location_inaccurate: "Location accuracy is too low. Try again outdoors.",
    location_denied: "Location permission was denied. You can change it in browser settings.",
    location_timeout: "Location request timed out. Please try again.",
    location_failed: "Unable to find your location. Please try again.",
    location_found: (name, accuracy) => `Nearest street: ${name}. Location accuracy: approximately ${accuracy} m.`,

    districts: "Districts",
    streets_network: "Street network",
    streets_network_title: "Toggle full street network lines",
    landmarks: "Estates & Landmarks",
    landmarks_title: "Toggle 151 housing estates, parks and bridges of Kraków",
    city_growth: "Growth 1910–Today",
    growth_title: "Territorial growth of Kraków",
    close_growth: "Close growth timeline",

    search_placeholder: "Search for a street or housing estate...",
    streets_count: (n) => `${n} streets loaded`,
    change_language: "Change language",
    map_style: "Map style:",
    drawer_title: "Object Details",
    empty_title: "Select an object",
    empty_desc: "Type a name above or click any highlighted line or point on the map.",
    patron_title: "Patron",
    wiki_bio_link: "View biography on Wikipedia",
    etymology_title: "Name Origin & Etymology",
    literal_meaning_label: "Literal meaning:",
    source_label: "Source:",
    open_doc: "Open document",
    resolution_title: "Local Municipal Act (City Council)",
    druk_sublabel: (num) => `${num}: official draft with rationale`,
    open_druk_pdf: "Open Council Draft with Rationale (PDF)",
    view_resolution_bip: "Resolution in BIP",
    download_resolution_pdf: "Resolution (PDF)",
    view_leg_path: "View legislative proceedings in BIP →",
    no_results: "No street or landmark found matching your search",
    resolution_badge: "Council Act",
    historical_badge: "Historical Name",
    metric_label: "Established:",
    city_border: "Kraków Border",
    fit_krakow: "Full City",
    footer_sources: "Data sources:",
    chip_wandy: "Wanda Estate",
    chip_florianska: "Floriańska St.",
    chip_szewska: "Szewska St.",
    chip_kwiatowa: "Kwiatowa St.",
    chip_szymborskiej: "Szymborska Park",
    chip_lema: "Lem St.",
    chip_slowackiego: "Słowacki Ave.",
    chip_dietla: "Dietl St.",
    digital_archive_nav: "Digital Archive"
  },
  de: {
    locate_me: "Mein Standort",
    location_unavailable: "Der Standort benötigt HTTPS oder localhost und Browserunterstützung.",
    location_loading: "Die Straßendaten werden noch geladen. Bitte gleich erneut versuchen.",
    location_wait: "Standort wird ermittelt…",
    location_outside: "Keine Straße in der Nähe in der Krakauer Datenbank gefunden.",
    location_inaccurate: "Der Standort ist zu ungenau. Bitte im Freien erneut versuchen.",
    location_denied: "Standortzugriff abgelehnt. Sie können dies in den Browsereinstellungen ändern.",
    location_timeout: "Zeitüberschreitung bei der Standortbestimmung. Bitte erneut versuchen.",
    location_failed: "Standort konnte nicht ermittelt werden. Bitte erneut versuchen.",
    location_found: (name, accuracy) => `Nächste Straße: ${name}. Standortgenauigkeit: etwa ${accuracy} m.`,

    districts: "Stadtbezirke",
    streets_network: "Straßennetz",
    streets_network_title: "Gesamtes Straßennetz ein-/ausblenden",
    landmarks: "Siedlungen & Orte",
    landmarks_title: "151 Siedlungen, Parks und Brücken Krakaus ein-/ausblenden",
    city_growth: "Entwicklung 1910–Heute",
    growth_title: "Gebietsentwicklung Krakaus",
    close_growth: "Zeitleiste schließen",

    search_placeholder: "Straßen- oder Siedlungsnamen suchen...",
    streets_count: (n) => `${n} Straßen geladen`,
    change_language: "Sprache ändern",
    map_style: "Kartenstil:",
    drawer_title: "Objektdetails",
    empty_title: "Objekt auswählen",
    empty_desc: "Geben Sie einen Namen ein oder klicken Sie auf eine Linie oder einen Punkt auf der Karte.",
    patron_title: "Namenspatron",
    wiki_bio_link: "Biografie auf Wikipedia ansehen",
    etymology_title: "Namensherkunft & Etymologie",
    literal_meaning_label: "Wörtliche Bedeutung:",
    source_label: "Quelle:",
    open_doc: "Dokument öffnen",
    resolution_title: "Kommunaler Rechtsakt (Stadtrat)",
    druk_sublabel: (num) => `${num}: Beschlussvorlage mit Begründung`,
    open_druk_pdf: "Beschlussvorlage mit Begründung (PDF)",
    view_resolution_bip: "Beschluss im BIP",
    download_resolution_pdf: "Beschluss (PDF)",
    view_leg_path: "Gesetzgebungsprozess im BIP ansehen →",
    no_results: "Keine passende Straße oder Siedlung gefunden",
    resolution_badge: "Stadtratsbeschluss",
    historical_badge: "Historischer Name",
    metric_label: "Ursprung:",
    city_border: "Stadtgrenze Krakau",
    fit_krakow: "Ganze Stadt",
    footer_sources: "Datenquellen:",
    chip_wandy: "Wanda-Siedlung",
    chip_florianska: "Floriańska-Straße",
    chip_szewska: "Szewska-Straße",
    chip_kwiatowa: "Kwiatowa-Straße",
    chip_szymborskiej: "Szymborska-Park",
    chip_lema: "Lem-Straße",
    chip_slowackiego: "Słowacki-Allee",
    chip_dietla: "Dietl-Straße",
    digital_archive_nav: "Digitales Archiv"
  }
};

class I18nManager {
  constructor() {
    this.currentLang = localStorage.getItem('krakow_lang') || 'pl';
    if (!['pl', 'en', 'de'].includes(this.currentLang)) {
      this.currentLang = 'pl';
    }
  }

  setLanguage(lang) {
    if (!['pl', 'en', 'de'].includes(lang)) return;
    this.currentLang = lang;
    localStorage.setItem('krakow_lang', lang);
    this.updateDOM();
    window.dispatchEvent(new CustomEvent('languagechange', { detail: { lang } }));
  }

  setupLanguagePickers() {
    document.querySelectorAll('.language-picker').forEach(picker => {
      const toggle = picker.querySelector('.language-picker-toggle');
      const menu = picker.querySelector('.language-picker-menu');
      if (!toggle || !menu) return;

      toggle.addEventListener('click', event => {
        event.stopPropagation();
        const shouldOpen = menu.classList.contains('hidden');
        this.closeLanguagePickers();
        menu.classList.toggle('hidden', !shouldOpen);
        toggle.setAttribute('aria-expanded', String(shouldOpen));
      });

      picker.querySelectorAll('[data-language-option]').forEach(option => {
        option.addEventListener('click', () => {
          this.setLanguage(option.getAttribute('data-language-option'));
          this.closeLanguagePickers();
        });
      });
    });

    document.addEventListener('click', () => this.closeLanguagePickers());
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') this.closeLanguagePickers();
    });
  }

  closeLanguagePickers() {
    document.querySelectorAll('.language-picker-menu').forEach(menu => menu.classList.add('hidden'));
    document.querySelectorAll('.language-picker-toggle').forEach(toggle => toggle.setAttribute('aria-expanded', 'false'));
  }

  t(key, ...args) {
    const dict = UI_TRANSLATIONS[this.currentLang] || UI_TRANSLATIONS.pl;
    const val = dict[key] || UI_TRANSLATIONS.pl[key] || key;
    if (typeof val === 'function') {
      return val(...args);
    }
    return val;
  }

  /**
   * Zwraca tekst dla danego pola z obsługą obiektów wielojęzycznych { pl, en, de }
   * oraz automatycznym fallbackiem do 'pl'.
   */
  localize(field, fallback = '') {
    if (!field) return fallback;
    if (typeof field === 'string') return field;
    if (typeof field === 'object') {
      return field[this.currentLang] || field.pl || field.en || fallback;
    }
    return String(field);
  }

  updateDOM() {
    // 1. Aktualizacja elementów z atrybutem data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = this.t(key);
      if (text) el.textContent = text;
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      el.title = this.t(el.getAttribute('data-i18n-title'));
    });

    // 2. Aktualizacja atrybutów placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const text = this.t(key);
      if (text) el.setAttribute('placeholder', text);
    });

    // 3. Aktualizacja kompaktowego przełącznika języka
    const languageMeta = {
      pl: {
    locate_me: "Moja lokalizacja",
    location_unavailable: "Lokalizacja wymaga HTTPS lub localhost i obsługi w przeglądarce.",
    location_loading: "Baza ulic jeszcze się ładuje. Spróbuj za chwilę.",
    location_wait: "Ustalanie lokalizacji…",
    location_outside: "Nie znaleziono ulicy w pobliżu w krakowskiej bazie.",
    location_inaccurate: "Odczyt lokalizacji jest zbyt niedokładny. Spróbuj ponownie na zewnątrz.",
    location_denied: "Brak zgody na lokalizację. Możesz ją zmienić w ustawieniach przeglądarki.",
    location_timeout: "Upłynął czas ustalania lokalizacji. Spróbuj ponownie.",
    location_failed: "Nie udało się ustalić lokalizacji. Spróbuj ponownie.",
    location_found: (name, accuracy) => `Najbliższa ulica: ${name}. Dokładność lokalizacji: około ${accuracy} m.`,

    districts: "Dzielnice",
    city_growth: "Rozwój 1910–Dziś",
    growth_title: "Rozwój terytorialny Krakowa",
    close_growth: "Zamknij oś rozwoju",
 flagClass: 'flag-pl', label: 'Polski' },
      en: {
    locate_me: "My location",
    location_unavailable: "Location requires HTTPS or localhost and browser support.",
    location_loading: "Street data is still loading. Please try again shortly.",
    location_wait: "Finding your location…",
    location_outside: "No nearby street was found in the Kraków dataset.",
    location_inaccurate: "Location accuracy is too low. Try again outdoors.",
    location_denied: "Location permission was denied. You can change it in browser settings.",
    location_timeout: "Location request timed out. Please try again.",
    location_failed: "Unable to find your location. Please try again.",
    location_found: (name, accuracy) => `Nearest street: ${name}. Location accuracy: approximately ${accuracy} m.`,

    districts: "Districts",
    city_growth: "Growth 1910–Today",
    growth_title: "Territorial growth of Kraków",
    close_growth: "Close growth timeline",
 flagClass: 'flag-gb', label: 'English' },
      de: {
    locate_me: "Mein Standort",
    location_unavailable: "Der Standort benötigt HTTPS oder localhost und Browserunterstützung.",
    location_loading: "Die Straßendaten werden noch geladen. Bitte gleich erneut versuchen.",
    location_wait: "Standort wird ermittelt…",
    location_outside: "Keine Straße in der Nähe in der Krakauer Datenbank gefunden.",
    location_inaccurate: "Der Standort ist zu ungenau. Bitte im Freien erneut versuchen.",
    location_denied: "Standortzugriff abgelehnt. Sie können dies in den Browsereinstellungen ändern.",
    location_timeout: "Zeitüberschreitung bei der Standortbestimmung. Bitte erneut versuchen.",
    location_failed: "Standort konnte nicht ermittelt werden. Bitte erneut versuchen.",
    location_found: (name, accuracy) => `Nächste Straße: ${name}. Standortgenauigkeit: etwa ${accuracy} m.`,

    districts: "Stadtbezirke",
    city_growth: "Entwicklung 1910–Heute",
    growth_title: "Gebietsentwicklung Krakaus",
    close_growth: "Zeitleiste schließen",
 flagClass: 'flag-de', label: 'Deutsch' }
    };
    const activeLanguage = languageMeta[this.currentLang];
    document.querySelectorAll('.current-language-flag').forEach(el => {
      el.classList.remove('flag-pl', 'flag-gb', 'flag-de');
      el.classList.add(activeLanguage.flagClass);
    });
    document.querySelectorAll('.language-picker-toggle').forEach(toggle => {
      toggle.setAttribute('aria-label', `${this.t('change_language')}: ${activeLanguage.label}`);
    });
    document.querySelectorAll('[data-language-option]').forEach(option => {
      option.setAttribute('aria-current', option.getAttribute('data-language-option') === this.currentLang ? 'true' : 'false');
      option.classList.toggle('bg-blue-50', option.getAttribute('data-language-option') === this.currentLang);
      option.classList.toggle('text-blue-700', option.getAttribute('data-language-option') === this.currentLang);
    });

    // 4. Zaktualizowanie atrybutu lang na znaczniku <html>
    document.documentElement.setAttribute('lang', this.currentLang);
  }
}

// Globalna instancja i18n
window.krakowI18n = new I18nManager();

document.addEventListener('DOMContentLoaded', () => {
  window.krakowI18n.setupLanguagePickers();
  window.krakowI18n.updateDOM();
});
