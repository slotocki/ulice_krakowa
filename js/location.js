/** One-shot device location; nearest street is calculated from the local GeoJSON. */
class StreetLocation {
  static nearest([lng, lat], streets) {
    const xScale = 111320 * Math.cos(lat * Math.PI / 180);
    let best = null;
    for (const street of streets) {
      const geom = street.geometry;
      const lines = geom?.type === 'LineString' ? [geom.coordinates] : geom?.type === 'MultiLineString' ? geom.coordinates : [];
      for (const line of lines) {
        for (let i = 1; i < line.length; i++) {
          const ax = (line[i-1][0] - lng) * xScale, ay = (line[i-1][1] - lat) * 111320;
          const bx = (line[i][0] - lng) * xScale, by = (line[i][1] - lat) * 111320;
          const dx = bx - ax, dy = by - ay;
          const t = Math.max(0, Math.min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy || 1)));
          const distance = Math.hypot(ax + t * dx, ay + t * dy);
          if (!best || distance < best.distance) best = { street, distance };
        }
      }
    }
    return best;
  }

  constructor(app) {
    this.app = app;
    this.button = document.createElement('button');
    this.button.type = 'button';
    this.button.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 1v4m0 14v4M1 12h4m14 0h4"/></svg>';
    const container = document.createElement('div');
    container.className = 'maplibregl-ctrl maplibregl-ctrl-group location-control';
    container.appendChild(this.button);
    app.map.addControl({onAdd: () => container, onRemove: () => container.remove()}, 'top-right');
    this.status = document.createElement('div');
    this.status.className = 'location-status';
    this.status.hidden = true;
    this.status.setAttribute('role', 'status');
    document.querySelector('main').appendChild(this.status);
    this.button.addEventListener('click', () => this.locate());
    window.addEventListener('languagechange', () => this.updateLanguage());
    this.updateLanguage();
  }

  updateLanguage() {
    this.button.title = window.krakowI18n.t('locate_me');
    this.button.setAttribute('aria-label', this.button.title);
    if (this.messageKey) this.status.textContent = window.krakowI18n.t(this.messageKey, ...this.messageArgs);
  }

  message(key, ...args) {
    this.messageKey = key;
    this.messageArgs = args;
    this.status.textContent = window.krakowI18n.t(key, ...args);
    this.status.hidden = false;
    clearTimeout(this.statusTimer);
    this.statusTimer = setTimeout(() => { this.status.hidden = true; }, 10000);
  }

  locate() {
    if (!navigator.geolocation || !window.isSecureContext) return this.message('location_unavailable');
    if (!this.app.streetsData) return this.message('location_loading');
    this.button.disabled = true;
    this.message('location_wait');
    navigator.geolocation.getCurrentPosition(position => {
      this.button.disabled = false;
      const {longitude, latitude, accuracy} = position.coords;
      const nearest = StreetLocation.nearest([longitude, latitude], this.app.streetsData.features);
      if (!nearest || nearest.distance > 150) return this.message('location_outside');
      if (!Number.isFinite(accuracy) || accuracy > 100) return this.message('location_inaccurate');
      this.marker?.remove();
      this.marker = new maplibregl.Marker({color: '#059669'}).setLngLat([longitude, latitude]).addTo(this.app.map);
      this.app.selectStreet(nearest.street);
      const name = window.krakowI18n.localize(nearest.street.properties.full_name || nearest.street.properties.name);
      this.message('location_found', name, Math.round(accuracy));
    }, error => {
      this.button.disabled = false;
      this.message(error.code === 1 ? 'location_denied' : error.code === 3 ? 'location_timeout' : 'location_failed');
    }, {enableHighAccuracy: true, timeout: 6000, maximumAge: 10000});
  }
}
