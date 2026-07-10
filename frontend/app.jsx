/* ─────────────────────────────────────────────────────────
   LifeEazy Hospital Vaccine Console — app.jsx
   React 18 · Hospital 3D Theme · RASA Socket.IO
   ───────────────────────────────────────────────────────── */
const { useState, useEffect, useRef, useCallback, Fragment } = React;

/* ── Constants ── */
const RASA_URL     = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? '' : 'https://tejas-vg-bot.hf.space';
const BOT_MSG_EVT  = 'bot_uttered';
const USER_MSG_EVT = 'user_uttered';

/* ── Helpers ── */
const now = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const getSessionId = () => {
  let sid = sessionStorage.getItem('rasa_sid');
  if (!sid) {
    sid = 'pt_' + Math.random().toString(36).slice(2, 10) + '_' + Date.now();
    sessionStorage.setItem('rasa_sid', sid);
  }
  return sid;
};

const esc = s =>
  String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

/* ── Text formatter ── */
const fmtHtml = text => {
  if (!text) return { __html: '' };
  if (
    text.includes('Hospital Name:') ||
    text.includes('available_capacity')
  ) {
    return { __html: `<pre>${esc(text)}</pre>` };
  }
  const html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
    .replace(/\n/g, '<br>');
  return { __html: html };
};

/* ── RASA text → structured hospital data ── */
const parseSlotData = text => {
  if (!text || !text.includes('Hospital Name:')) return null;
  const blocks = text.split(/\*{8,}/);
  const facilities = [];
  blocks.forEach(b => {
    const t = b.trim();
    if (!t.includes('Hospital Name:')) return;
    const fac = { name:'', address:'', pincode:'', dose1:null, dose2:null,
                   total:null, ageLimit:null, slots:[], state:'', district:'',
                   lat:null, lon:null };
    t.split('\n').forEach(line => {
      const i = line.indexOf(':');
      if (i < 0) return;
      const k = line.slice(0, i).trim().toLowerCase();
      const v = line.slice(i + 1).trim();
      if (k === 'hospital name')              fac.name    = v;
      else if (k === 'address')               fac.address = v;
      else if (k === 'pincode')               fac.pincode = v;
      else if (k === 'available_capacity_dose1') fac.dose1 = v;
      else if (k === 'available_capacity_dose2') fac.dose2 = v;
      else if (k === 'available_capacity')    fac.total   = v;
      else if (k === 'min_age_limit')         fac.ageLimit = v;
      else if (k === 'time slots')            fac.slots   = v.replace(/[[\]'"]/g,'').split(',').map(s=>s.trim()).filter(Boolean);
      else if (k === 'state_name')            fac.state    = v;
      else if (k === 'district_name')         fac.district = v;
      else if (k === 'latitude')              fac.lat      = parseFloat(v);
      else if (k === 'longitude')             fac.lon      = parseFloat(v);
    });
    if (fac.name) facilities.push(fac);
  });
  return facilities.length ? { facilities } : null;
};

/* ── 3-D card tilt hook ── */
const useTilt = (ref, maxDeg = 10) => {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const move = e => {
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width  - .5;
      const y = (e.clientY - r.top)  / r.height - .5;
      el.style.transform = `perspective(600px) rotateY(${x*maxDeg*2}deg) rotateX(${-y*maxDeg}deg) translateY(-3px) translateZ(10px)`;
    };
    const leave = () => {
      el.style.transform = '';
      el.style.transition = 'transform .45s cubic-bezier(.25,.8,.25,1)';
      setTimeout(() => { el.style.transition = ''; }, 450);
    };
    el.addEventListener('mousemove', move);
    el.addEventListener('mouseleave', leave);
    return () => { el.removeEventListener('mousemove', move); el.removeEventListener('mouseleave', leave); };
  }, []);
};

/* ════════════════════════════════════════════
   SVG ICON COMPONENTS
   ════════════════════════════════════════════ */
const CrossIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    <line x1="12" y1="8" x2="12" y2="16"/><line x1="9" y1="12" x2="15" y2="12"/>
  </svg>
);
const PinIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
  </svg>
);
const DistIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/>
    <line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/>
  </svg>
);
const GpsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
    <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
  </svg>
);
const MenuIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/>
  </svg>
);
const TrashIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
);
const PlusIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);
const SendIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const FileIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="14" y2="17"/>
  </svg>
);

/* ════════════════════════════════════════════
   3-D HOSPITAL CROSS (Welcome animation)
   ════════════════════════════════════════════ */
const HospitalCross3D = ({ stageRef }) => (
  <div className="hospital-3d-stage">
    <div className="cross-3d-container" ref={stageRef}>
      {/* Glow ring */}
      <div className="cross-glow-ring" />
      {/* Orbiting rings */}
      <div className="orbit"><div className="orbit-dot" /></div>
      <div className="orbit orbit-2"><div className="orbit-dot" /></div>
      {/* Cross bars */}
      <div className="cross-h" />
      <div className="cross-v" />
      {/* Floating info mini-cards */}
      <div className="float-card float-card-1">
        <span className="float-card-dot" />Live Slots
      </div>
      <div className="float-card float-card-2">
        <span className="float-card-dot" />CoWin API v2
      </div>
      <div className="float-card float-card-3">
        <span className="float-card-dot" />AI Triage
      </div>
    </div>
  </div>
);

/* ════════════════════════════════════════════
   ECG WAVE in header
   ════════════════════════════════════════════ */
const EcgWave = () => (
  <div className="ecg-wave-wrap">
    {/* Repeating SVG path that looks like an ECG trace */}
    <svg className="ecg-wave" viewBox="0 0 900 28" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
      <path
        d="M0 14 L60 14 L70 14 L75 4 L80 24 L85 2 L90 26 L95 14 L110 14
           L170 14 L180 14 L185 4 L190 24 L195 2 L200 26 L205 14 L220 14
           L280 14 L290 14 L295 4 L300 24 L305 2 L310 26 L315 14 L330 14
           L390 14 L400 14 L405 4 L410 24 L415 2 L420 26 L425 14 L440 14
           L500 14 L510 14 L515 4 L520 24 L525 2 L530 26 L535 14 L550 14
           L610 14 L620 14 L625 4 L630 24 L635 2 L640 26 L645 14 L660 14
           L720 14 L730 14 L735 4 L740 24 L745 2 L750 26 L755 14 L770 14
           L830 14 L840 14 L845 4 L850 24 L855 2 L860 26 L865 14 L880 14 L900 14"
        stroke="#00857c"
        strokeWidth="1.8"
        strokeOpacity="0.35"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  </div>
);

/* ════════════════════════════════════════════
   SIDEBAR COMPONENT
   ════════════════════════════════════════════ */
const Sidebar = ({ connClass, connLabel, onMode }) => {
  const vitalsRef = useRef(null);
  useTilt(vitalsRef, 8);

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-top">
        <div className="logo-cross"><CrossIcon /></div>
        <div className="logo-label">
          MAYDEN SMARTHEALTH
          <small>PVT LTD · Vaccine Console</small>
        </div>
      </div>

      {/* Search Modes */}
      <div className="sidebar-section">
        <div className="section-label">Select Search Mode</div>
        <div className="mode-list">
          {[
            { label: 'Area Pincode',     desc: '6-digit postal code scan',  icon: <PinIcon />,  msg: '/pincode'  },
            { label: 'District ID',      desc: 'Scan by district region',   icon: <DistIcon />, msg: '/district' },
            { label: 'GPS Coordinates',  desc: 'Nearest slots via lat/lon', icon: <GpsIcon />,  msg: '/location' },
          ].map(m => (
            <button key={m.msg} className="mode-btn" onClick={() => onMode(m.msg)}>
              <div className="mode-icon">{m.icon}</div>
              <div className="mode-text">
                <span className="mode-title">{m.label}</span>
                <span className="mode-desc">{m.desc}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Vitals Card */}
      <div className="vitals-card" ref={vitalsRef}>
        <div className="vitals-title">System Vitals</div>
        <div className="vitals-row">
          <span className="vitals-key">Engine</span>
          <span className="vitals-val">RASA v2.8</span>
        </div>
        <div className="vitals-row">
          <span className="vitals-key">API</span>
          <span className="vitals-val">CoWin Public v2</span>
        </div>
        <div className="vitals-row">
          <span className="vitals-key">Latency</span>
          <div className="vitals-pulse">
            <span className="vitals-pulse-dot" />
            <span className="vitals-val">Optimal</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="conn-row">
          <span className={`conn-dot ${connClass === 'connected' ? 'online' : connClass === 'connecting' ? 'linking' : ''}`} />
          <span className="conn-label">{connLabel}</span>
        </div>
        <div className="conn-endpoint">{RASA_URL || 'ws://localhost:5005'}</div>
        <div className="footer-meta">
          <span>MAYDEN SMARTHEALTH v2.8</span>
          <a href="https://apisetu.gov.in/directory/api/cowin/" target="_blank" rel="noopener">CoWin Official Docs</a>
        </div>
      </div>
    </aside>
  );
};

/* ════════════════════════════════════════════
   WELCOME SCREEN
   ════════════════════════════════════════════ */
const WelcomeScreen = ({ onMode }) => {
  const stageRef   = useRef(null);
  const screenRef  = useRef(null);
  const card1 = useRef(null);
  const card2 = useRef(null);
  const card3 = useRef(null);
  const cardRefs = [card1, card2, card3];
  useTilt(card1, 7);
  useTilt(card2, 7);
  useTilt(card3, 7);

  /* Mouse parallax on the 3-D cross stage */
  useEffect(() => {
    const scr = screenRef.current;
    const stg = stageRef.current;
    if (!scr || !stg) return;
    const onMove = e => {
      const r  = scr.getBoundingClientRect();
      const dx = (e.clientX - r.left  - r.width  / 2) / (r.width  / 2);
      const dy = (e.clientY - r.top   - r.height / 2) / (r.height / 2);
      stg.style.transform = `rotateX(${-dy * 14}deg) rotateY(${dx * 18}deg)`;
    };
    const onLeave = () => {
      stg.style.transform = '';
      stg.style.transition = 'transform .6s ease';
      setTimeout(() => { stg.style.transition = ''; }, 600);
    };
    scr.addEventListener('mousemove', onMove);
    scr.addEventListener('mouseleave', onLeave);
    return () => {
      scr.removeEventListener('mousemove', onMove);
      scr.removeEventListener('mouseleave', onLeave);
    };
  }, []);

  const modes = [
    { label: 'Search by PIN',      desc: 'Enter a 6-digit pincode to scan local vaccination centres.',  icon: <PinIcon />,  msg: '/pincode'  },
    { label: 'Search by District', desc: 'Scan every registered centre inside a selected district.',     icon: <DistIcon />, msg: '/district' },
    { label: 'GPS Search',         desc: 'Provide coordinates to find slots closest to your location.',  icon: <GpsIcon />,  msg: '/location' },
  ];

  return (
    <div className="welcome-wrap" ref={screenRef}>
      <HospitalCross3D stageRef={stageRef} />

      <h1 className="welcome-headline">How can I help you today?</h1>
      <p className="welcome-sub">
        Choose a vaccination slot search mode or type your query in the input below.
      </p>

      <div className="welcome-grid">
        {modes.map((m, i) => (
          <button key={m.msg} className="wcard" ref={cardRefs[i]} onClick={() => onMode(m.msg)}>
            <div className="wcard-icon">{m.icon}</div>
            <h4>{m.label}</h4>
            <p>{m.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
};

/* ════════════════════════════════════════════
   MESSAGE ROW
   ════════════════════════════════════════════ */
const MessageRow = ({ msg, onChoice }) => {
  if (msg.type === 'system') {
    return (
      <div className="sys-row">
        <div className="sys-chip">{msg.text}</div>
      </div>
    );
  }
  const isUser = msg.type === 'user';
  return (
    <div className={`msg-row ${isUser ? 'user-row' : 'bot-row'}`}>
      <div className="msg-inner">
        <div className={`msg-avatar ${isUser ? 'user-av' : 'bot-av'}`}>
          {isUser ? 'U' : 'AI'}
        </div>
        <div className="msg-body">
          {msg.image ? (
            <img src={msg.image} style={{ maxWidth:'100%', borderRadius:'8px', border:'1px solid var(--border)', marginTop:'6px' }} />
          ) : (
            <div dangerouslySetInnerHTML={fmtHtml(msg.text)} />
          )}

          {msg.buttons && msg.buttons.length > 0 && (
            <div className="qr-row">
              {msg.buttons.map((b, i) => (
                <button key={i} className="qr-btn" onClick={() => onChoice(b.payload)}>
                  {b.title}
                </button>
              ))}
            </div>
          )}

          <div className="msg-time-row">
            <span>{isUser ? 'Console Operator' : 'Vaccine Assistant'}</span>
            <span>{msg.time}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ════════════════════════════════════════════
   DATA INSPECTOR PANEL
   ════════════════════════════════════════════ */
const DataInspector = ({ active, data, searchMethod, userCoords, activeHospitalIdx, setActiveHospitalIdx, onBook }) => {
  const mapInstanceRef = useRef(null);
  const markersGroupRef = useRef(null);
  const routeLineRef = useRef(null);

  useEffect(() => {
    if (!active || !data || !data.facilities || data.facilities.length === 0) return;

    const mapEl = document.getElementById('live-map');
    if (!mapEl) return;

    // Initialize Leaflet map instance if not already loaded
    if (!mapInstanceRef.current) {
      const map = L.map('live-map', {
        zoomControl: true,
        attributionControl: false
      });
      
      const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
      });
      
      const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19
      });

      // Default to Streets
      streets.addTo(map);

      const baseMaps = {
        "Detailed Streets": streets,
        "Satellite Imagery": satellite
      };
      
      L.control.layers(baseMaps, null, { position: 'topright' }).addTo(map);

      mapInstanceRef.current = map;
      markersGroupRef.current = L.featureGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const group = markersGroupRef.current;
    group.clearLayers();

    // Map Center coords
    let centerLat = 13.0827; // Chennai Default
    let centerLon = 80.2707;

    // User Blue Pulse Marker
    if (userCoords && userCoords.lat && userCoords.lon) {
      centerLat = userCoords.lat;
      centerLon = userCoords.lon;

      const userIcon = L.divIcon({
        className: 'leaflet-user-pulse',
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      L.marker([centerLat, centerLon], { icon: userIcon })
        .bindPopup("Your Location")
        .addTo(group);
    }

    // Add hospital markers
    const { facilities } = data;
    facilities.forEach((f, idx) => {
      if (!f.lat || !f.lon) return;
      const isSelected = idx === activeHospitalIdx;

      // Hospital Cross Custom marker HTML
      const crossHtml = `
        <div class="leaflet-hospital-icon" style="${isSelected ? 'background:#00857c;color:#fff;border-color:#006b63;transform:scale(1.2);' : ''} width:24px;height:24px;display:flex;align-items:center;justify-content:center;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,.15);">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" style="width:12px;height:12px;${isSelected ? 'color:#fff;' : 'color:#00857c;'}">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </div>
      `;

      const hospitalIcon = L.divIcon({
        html: crossHtml,
        className: 'leaflet-custom-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      const marker = L.marker([f.lat, f.lon], { icon: hospitalIcon })
        .bindPopup(`<b>${f.name}</b><br><small>${f.address}</small>`)
        .addTo(group);

      if (isSelected) {
        marker.openPopup();
      }

      marker.on('click', () => {
        setActiveHospitalIdx(idx);
      });
    });

    // Draw Route (Ola / Uber Curved animation route)
    if (routeLineRef.current) {
      map.removeLayer(routeLineRef.current);
      routeLineRef.current = null;
    }

    const activeFac = facilities[activeHospitalIdx];
    if (userCoords && userCoords.lat && userCoords.lon && activeFac && activeFac.lat && activeFac.lon) {
      const p1 = [userCoords.lat, userCoords.lon];
      const p2 = [activeFac.lat, activeFac.lon];

      // Intermediate curved path calculations for smooth arc line
      const midLat = (p1[0] + p2[0]) / 2 + (p2[1] - p1[1]) * 0.04;
      const midLon = (p1[1] + p2[1]) / 2 - (p2[0] - p1[0]) * 0.04;

      const routeLine = L.polyline([p1, [midLat, midLon], p2], {
        className: 'leaflet-route-flow',
        color: '#1a56db',
        weight: 4,
        opacity: 0.8
      }).addTo(map);

      routeLineRef.current = routeLine;
    }

    // Zoom and pan to selected hospital if clicked, otherwise fit bounds
    if (activeFac && activeFac.lat && activeFac.lon) {
      map.setView([activeFac.lat, activeFac.lon], 14, { animate: true });
    } else if (group.getBounds().isValid()) {
      map.fitBounds(group.getBounds(), { padding: [40, 40] });
    } else {
      map.setView([centerLat, centerLon], 13);
    }
  }, [active, data, userCoords, activeHospitalIdx]);

  if (!active || !data) {
    return (
      <aside className="inspector">
        <div className="inspector-header">
          <div>
            <div className="inspector-title">Live Data Inspector</div>
            <div className="inspector-sub">Inactive Session</div>
          </div>
        </div>
        <div className="inspector-body">
          <div className="empty-state">
            <div className="empty-icon"><FileIcon /></div>
            <h3>No Active Queries</h3>
            <p>Run a pincode, district, or GPS search via the assistant. Detailed slot data will populate here in real-time.</p>
          </div>
        </div>
      </aside>
    );
  }

  const { facilities } = data;
  const first = facilities[0] || {};

  return (
    <aside className="inspector">
      <div className="inspector-header">
        <div>
          <div className="inspector-title">Live Data Inspector</div>
          <div className="inspector-sub">Active Monitoring</div>
        </div>
        <span className="live-tag">Live</span>
      </div>

      {/* Ola/Uber Style Interactive Map */}
      <div className="map-section">
        <div id="live-map"></div>
      </div>

      <div className="inspector-body">
        {/* Active query card */}
        <div className="query-card">
          <div className="qcard-head">
            <span className="qcard-label">Active Parameter Set</span>
          </div>
          <div className="q-row"><span className="q-key">Method</span><span className="q-val">{searchMethod}</span></div>
          {first.pincode && <div className="q-row"><span className="q-key">Pincode</span><span className="q-val">PIN {first.pincode}</span></div>}
          {(first.district || first.state) && (
            <div className="q-row">
              <span className="q-key">Region</span>
              <span className="q-val">{[first.district, first.state].filter(Boolean).join(', ')}</span>
            </div>
          )}
        </div>

        {/* Results header */}
        <div className="results-bar">
          <h3>Vaccination Facilities</h3>
          <span className="count-badge">{facilities.length} Found</span>
        </div>

        {/* Facility cards */}
        {facilities.map((f, idx) => (
          <FacilityCard
            key={idx}
            f={f}
            idx={idx}
            isSelected={idx === activeHospitalIdx}
            onSelect={setActiveHospitalIdx}
            onBook={onBook}
          />
        ))}
      </div>
    </aside>
  );
};

const FacilityCard = ({ f, idx, isSelected, onSelect, onBook }) => {
  const ref = useRef(null);
  useTilt(ref, 5);
  return (
    <div
      className="fac-card"
      ref={ref}
      onClick={() => onSelect(idx)}
      style={{
        borderLeft: isSelected ? '4px solid #00857c' : '1px solid var(--border)',
        background: isSelected ? 'var(--green-light)' : '#fff',
        cursor: 'pointer'
      }}
    >
      <div className="fac-name">{f.name}</div>
      <div className="fac-addr">{f.address || f.blockName || 'Local Vaccination Centre'}</div>

      {(f.total != null || f.ageLimit != null) && (
        <div className="fac-grid">
          <div className="fac-cell">
            <span className="fac-lbl">Age Limit</span>
            <span className="tag-age">{f.ageLimit ? f.ageLimit + '+' : 'All Ages'}</span>
          </div>
          <div className="fac-cell">
            <span className="fac-lbl">Total Doses</span>
            <span className="tag-cap">{f.total || 0} Available</span>
          </div>
          {f.dose1 != null && (
            <div className="fac-cell">
              <span className="fac-lbl">Dose 1</span>
              <span className="fac-val">{f.dose1}</span>
            </div>
          )}
          {f.dose2 != null && (
            <div className="fac-cell">
              <span className="fac-lbl">Dose 2</span>
              <span className="fac-val">{f.dose2}</span>
            </div>
          )}
        </div>
      )}

      {f.slots && f.slots.length > 0 && (
        <div className="fac-slots">
          <div className="fac-slots-lbl">Appointment Timings</div>
          <div className="slot-pills">
            {f.slots.map((s, i) => <span key={i} className="slot-pill">{s}</span>)}
          </div>
        </div>
      )}

      {isSelected && (
        <button
          onClick={(e) => { e.stopPropagation(); onBook(f); }}
          style={{
            marginTop: '12px', width: '100%', padding: '10px',
            background: 'var(--green)', color: '#fff', borderRadius: '8px',
            fontWeight: '600', fontSize: '.84rem', textAlign: 'center', border:'none',
            boxShadow: '0 2px 6px rgba(0, 133, 124, 0.25)', cursor:'pointer'
          }}
        >
          Book Appointment
        </button>
      )}
    </div>
  );
};

/* ════════════════════════════════════════════
   VACCINE SLOT BOOKING MODAL
   ════════════════════════════════════════════ */
const BookingModal = ({ hospital, onClose, onConfirm, confirmedData }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [age, setAge] = useState('');
  const [idType, setIdType] = useState('Aadhaar Card');
  const [idNo, setIdNo] = useState('');
  const [vaccine, setVaccine] = useState('Covishield');
  const [dose, setDose] = useState('Dose 1');
  const [timeSlot, setTimeSlot] = useState(hospital?.slots?.[0] || '09:00 AM - 12:00 PM');

  if (!hospital) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name || !email || !age || !idNo) return;
    const refCode = 'LFEZ-' + Math.floor(100000 + Math.random() * 900000) + '-TN';
    onConfirm({
      name, email, age, idType, idNo, vaccine, dose, timeSlot, refCode,
      hospitalName: hospital.name,
      hospitalAddress: hospital.address
    });
  };

  return (
    <div style={{
      position:'fixed', inset:0, zIndex:10000,
      background:'rgba(13,31,45,.6)', backdropFilter:'blur(5px)',
      display:'flex', alignItems:'center', justifyContent:'center', padding:'20px'
    }}>
      <div style={{
        background:'#fff', borderRadius:'18px', width:'100%', maxWidth:'480px',
        boxShadow:'0 24px 64px rgba(0,0,0,.25)', overflow:'hidden',
        maxHeight:'90vh', display:'flex', flexDirection:'column'
      }}>
        
        {confirmedData ? (
          /* Confirmed Booking Ticket Visual */
          <div style={{ padding:'0', display:'flex', flexDirection:'column', overflowY:'auto' }}>
            <div style={{ background:'linear-gradient(135deg,#00857c,#006b63)', padding:'24px', color:'#fff', textAlign:'center', position:'relative' }}>
              <div style={{ width:'48px', height:'48px', background:'rgba(255,255,255,0.2)', borderRadius:'50%', display:'flex', alignItems:'center', margin:'0 auto 12px', justifyContent:'center' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" style={{ width:'24px', height:'24px' }}>
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <h2 style={{ fontFamily:"'Syne',sans-serif", fontSize:'1.4rem', fontWeight:800 }}>Booking Confirmed</h2>
              <p style={{ fontSize:'.82rem', opacity:.8, marginTop:'4px' }}>Reference ID: {confirmedData.refCode}</p>
            </div>
            
            <div style={{ padding:'24px', flex:1 }}>
              {/* Ticket details */}
              <div style={{ border:'2px dashed #dde4ed', borderRadius:'12px', padding:'16px', background:'#f8fbff', position:'relative' }}>
                <div style={{ fontSize:'.68rem', fontWeight:700, textTransform:'uppercase', color:'#00857c', letterSpacing:'.05em' }}>Facility</div>
                <div style={{ fontSize:'.95rem', fontWeight:700, color:'#0d1f2d', marginTop:'2px' }}>{confirmedData.hospitalName}</div>
                <div style={{ fontSize:'.78rem', color:'#4a6070', marginTop:'2px' }}>{confirmedData.hospitalAddress}</div>
                
                <hr style={{ border:'none', borderTop:'1px dashed #dde4ed', margin:'12px 0' }} />
                
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px 6px' }}>
                  <div>
                    <span style={{ fontSize:'.68rem', color:'#8fa5b3', textTransform:'uppercase', display:'block' }}>Beneficiary</span>
                    <span style={{ fontSize:'.86rem', fontWeight:600, color:'#1e3a4a' }}>{confirmedData.name} ({confirmedData.age} yrs)</span>
                  </div>
                  <div>
                    <span style={{ fontSize:'.68rem', color:'#8fa5b3', textTransform:'uppercase', display:'block' }}>Vaccine & Dose</span>
                    <span style={{ fontSize:'.86rem', fontWeight:600, color:'#1e3a4a' }}>{confirmedData.vaccine} - {confirmedData.dose}</span>
                  </div>
                  <div>
                    <span style={{ fontSize:'.68rem', color:'#8fa5b3', textTransform:'uppercase', display:'block' }}>Time Slot</span>
                    <span style={{ fontSize:'.86rem', fontWeight:600, color:'#1e3a4a' }}>{confirmedData.timeSlot}</span>
                  </div>
                  <div>
                    <span style={{ fontSize:'.68rem', color:'#8fa5b3', textTransform:'uppercase', display:'block' }}>Govt ID ({confirmedData.idType})</span>
                    <span style={{ fontSize:'.86rem', fontWeight:600, color:'#1e3a4a' }}>XXXX-XXXX-{confirmedData.idNo.slice(-4)}</span>
                  </div>
                </div>

                <hr style={{ border:'none', borderTop:'1px dashed #dde4ed', margin:'12px 0' }} />
                
                {/* QR Code (Dynamic API) */}
                <div style={{ display:'flex', alignItems:'center', gap:'14px' }}>
                  <div style={{ background:'#fff', border:'1px solid #dde4ed', padding:'6px', borderRadius:'8px', display:'flex', alignItems:'center' }}>
                    <img 
                      src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&color=00857c&data=${encodeURIComponent(
                        `MAYDEN SMARTHEALTH PVT LTD\n\nReference ID: ${confirmedData.refCode}\nPatient Name: ${confirmedData.name}\nAge: ${confirmedData.age}\nVaccine: ${confirmedData.vaccine} - ${confirmedData.dose}\nTime Slot: ${confirmedData.timeSlot}\nHospital: ${confirmedData.hospitalName}`
                      )}`}
                      alt="Booking QR Code" 
                      style={{ width:'70px', height:'70px', display:'block' }} 
                    />
                  </div>
                  <div>
                    <div style={{ fontSize:'.8rem', fontWeight:700, color:'#0d1f2d' }}>Scan Appointment Ticket</div>
                    <div style={{ fontSize:'.74rem', color:'#4a6070', marginTop:'2px', lineHeight:1.3 }}>Present this ticket at the verification counter along with original ID.</div>
                  </div>
                </div>
              </div>

              <button onClick={onClose} style={{
                marginTop:'20px', width:'100%', padding:'12px', background:'#00857c',
                color:'#fff', border:'none', borderRadius:'10px', fontWeight:700,
                fontSize:'.9rem', cursor:'pointer'
              }}>Done</button>
            </div>
          </div>
        ) : (
          /* Slot Booking Form */
          <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', overflowY:'auto' }}>
            <div style={{ background:'linear-gradient(135deg,#00857c,#006b63)', padding:'18px 22px', color:'#fff' }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <span style={{ fontSize:'.68rem', fontWeight:700, textTransform:'uppercase', background:'rgba(255,255,255,0.18)', padding:'2px 8px', borderRadius:'6px' }}>Slot Booking Portal</span>
                <button type="button" onClick={onClose} style={{ color:'#fff', opacity:.8, fontSize:'1.2rem', cursor:'pointer' }}>&times;</button>
              </div>
              <h2 style={{ fontFamily:"'Syne',sans-serif", fontSize:'1.1rem', fontWeight:800, marginTop:'6px' }}>{hospital.name}</h2>
              <p style={{ fontSize:'.78rem', opacity:.8, marginTop:'2px' }}>{hospital.address}</p>
            </div>

            <div style={{ padding:'20px 22px', display:'flex', flexDirection:'column', gap:'14px' }}>
              {/* Name */}
              <div>
                <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'5px' }}>Beneficiary Name</label>
                <input required value={name} onChange={e=>setName(e.target.value)} placeholder="Full Name (as in Govt ID)"
                  style={{ width:'100%', padding:'10px 12px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.88rem', outline:'none', background:'#f8fbff' }} />
              </div>

              {/* Email */}
              <div>
                <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'5px' }}>Email Address</label>
                <input required type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email ID for booking ticket"
                  style={{ width:'100%', padding:'10px 12px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.88rem', outline:'none', background:'#f8fbff' }} />
              </div>

              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px' }}>
                {/* Age */}
                <div>
                  <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'5px' }}>Age (Years)</label>
                  <input required type="number" min="18" max="120" value={age} onChange={e=>setAge(e.target.value)} placeholder="Age"
                    style={{ width:'100%', padding:'10px 12px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.88rem', outline:'none', background:'#f8fbff' }} />
                </div>
                {/* Dose */}
                <div>
                  <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'5px' }}>Dose Type</label>
                  <select value={dose} onChange={e=>setDose(e.target.value)}
                    style={{ width:'100%', padding:'10px 12px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.88rem', outline:'none', background:'#f8fbff' }}>
                    <option>Dose 1</option>
                    <option>Dose 2</option>
                  </select>
                </div>
              </div>

              {/* Vaccine Selection cards */}
              <div>
                <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'6px' }}>Select Vaccine Type</label>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:'8px' }}>
                  {[
                    { name:'Covishield', desc:'Adenovirus vector' },
                    { name:'Covaxin', desc:'Inactivated virus' },
                    { name:'Sputnik V', desc:'Vector platform' }
                  ].map(v => (
                    <div key={v.name}
                      onClick={() => setVaccine(v.name)}
                      style={{
                        border: vaccine === v.name ? '2px solid #00857c' : '1px solid #dde4ed',
                        background: vaccine === v.name ? '#e6f7f6' : '#fff',
                        borderRadius:'8px', padding:'8px', cursor:'pointer',
                        textAlign:'center'
                      }}>
                      <div style={{ fontSize:'.82rem', fontWeight:700, color: vaccine === v.name ? '#00857c' : '#0d1f2d' }}>{v.name}</div>
                      <div style={{ fontSize:'.58rem', color:'#8fa5b3', marginTop:'2px' }}>{v.desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Time Slots */}
              <div>
                <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'6px' }}>Available Time Slot</label>
                <div style={{ display:'flex', flexWrap:'wrap', gap:'6px' }}>
                  {(hospital.slots && hospital.slots.length > 0 ? hospital.slots : ['09:00 AM - 12:00 PM', '02:00 PM - 05:00 PM']).map(s => (
                    <div key={s}
                      onClick={() => setTimeSlot(s)}
                      style={{
                        border: timeSlot === s ? '1.5px solid #00857c' : '1px solid #dde4ed',
                        background: timeSlot === s ? 'var(--green-light)' : '#f4f7fa',
                        color: timeSlot === s ? '#00857c' : '#4a6070',
                        borderRadius:'6px', padding:'6px 12px', fontSize:'.76rem', fontWeight:600,
                        cursor:'pointer'
                      }}>
                      {s}
                    </div>
                  ))}
                </div>
              </div>

              {/* ID Verification */}
              <div style={{ display:'grid', gridTemplateColumns:'1.2fr 1.8fr', gap:'8px' }}>
                <div>
                  <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'5px' }}>Govt Photo ID</label>
                  <select value={idType} onChange={e=>setIdType(e.target.value)}
                    style={{ width:'100%', padding:'10px 10px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.85rem', outline:'none', background:'#f8fbff' }}>
                    <option>Aadhaar Card</option>
                    <option>PAN Card</option>
                    <option>Driving License</option>
                    <option>Passport</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize:'.72rem', fontWeight:700, color:'#4a6070', textTransform:'uppercase', display:'block', marginBottom:'5px' }}>Photo ID Number</label>
                  <input required value={idNo} onChange={e=>setIdNo(e.target.value)} placeholder="Govt ID card number"
                    style={{ width:'100%', padding:'10px 12px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.88rem', outline:'none', background:'#f8fbff' }} />
                </div>
              </div>

              <div style={{ display:'flex', gap:'8px', marginTop:'8px' }}>
                <button type="button" onClick={onClose} style={{
                  flex:1, padding:'11px', background:'#f4f7fa', color:'#4a6070',
                  border:'1px solid #dde4ed', borderRadius:'10px', fontWeight:600, fontSize:'.88rem', cursor:'pointer'
                }}>Cancel</button>
                <button type="submit" style={{
                  flex:2, padding:'11px', background:'#00857c', color:'#fff',
                  border:'none', borderRadius:'10px', fontWeight:700, fontSize:'.88rem',
                  boxShadow:'0 4px 12px rgba(0, 133, 124, 0.2)', cursor:'pointer'
                }}>Confirm Vaccination Slot</button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

/* ════════════════════════════════════════════
   GPS PERMISSION MODAL
   ════════════════════════════════════════════ */
const GpsModal = ({ state, coords, error, onAllow, onManual, onClose }) => {
  const [manLat, setManLat] = useState('');
  const [manLon, setManLon] = useState('');

  if (!state) return null;

  return (
    <div style={{
      position:'fixed', inset:0, zIndex:9999,
      background:'rgba(13,31,45,.55)', backdropFilter:'blur(4px)',
      display:'flex', alignItems:'center', justifyContent:'center', padding:'20px'
    }}>
      <div style={{
        background:'#fff', borderRadius:'16px', width:'100%', maxWidth:'400px',
        boxShadow:'0 24px 64px rgba(0,0,0,.22)', overflow:'hidden'
      }}>
        {/* Header */}
        <div style={{ background:'linear-gradient(135deg,#00857c,#006b63)', padding:'20px 22px', color:'#fff' }}>
          <div style={{ fontFamily:"'Syne',sans-serif", fontSize:'1.05rem', fontWeight:800 }}>GPS Location Access</div>
          <div style={{ fontSize:'.78rem', opacity:.75, marginTop:'3px' }}>Required to find nearest vaccination centres</div>
        </div>

        <div style={{ padding:'20px 22px' }}>
          {state === 'prompt' && (
            <>
              <p style={{ fontSize:'.86rem', color:'#1e3a4a', lineHeight:1.55, marginBottom:'16px' }}>
                To find vaccination centres closest to you, please allow location access. Your coordinates are used only for this query and are never stored.
              </p>
              <button onClick={onAllow} style={{
                width:'100%', padding:'11px', background:'#00857c', color:'#fff',
                border:'none', borderRadius:'10px', fontWeight:700, fontSize:'.88rem',
                cursor:'pointer', marginBottom:'8px'
              }}>Allow Location Access</button>
              <button onClick={() => onManual()} style={{
                width:'100%', padding:'10px', background:'#f4f7fa', color:'#4a6070',
                border:'1px solid #dde4ed', borderRadius:'10px', fontWeight:600,
                fontSize:'.84rem', cursor:'pointer'
              }}>Enter Coordinates Manually</button>
            </>
          )}

          {state === 'loading' && (
            <div style={{ textAlign:'center', padding:'24px 0', color:'#00857c' }}>
              <div style={{ fontSize:'2rem', marginBottom:'12px', animation:'spin 1s linear infinite', display:'inline-block' }}>+</div>
              <p style={{ fontSize:'.86rem', color:'#4a6070' }}>Detecting your location…</p>
            </div>
          )}

          {state === 'success' && coords && (
            <>
              <div style={{ background:'#e6f7f6', border:'1px solid rgba(0,133,124,.25)', borderRadius:'10px', padding:'14px 16px', marginBottom:'16px' }}>
                <div style={{ fontSize:'.7rem', fontWeight:700, textTransform:'uppercase', letterSpacing:'.05em', color:'#00857c', marginBottom:'8px' }}>Detected Location</div>
                <div style={{ fontSize:'.88rem', fontWeight:600, color:'#0d1f2d' }}>Lat: {coords.lat.toFixed(5)}</div>
                <div style={{ fontSize:'.88rem', fontWeight:600, color:'#0d1f2d' }}>Lon: {coords.lon.toFixed(5)}</div>
                <div style={{ fontSize:'.74rem', color:'#4a6070', marginTop:'6px' }}>Accuracy: ±{Math.round(coords.accuracy)}m</div>
              </div>
              <button onClick={() => onManual(coords)} style={{
                width:'100%', padding:'11px', background:'#00857c', color:'#fff',
                border:'none', borderRadius:'10px', fontWeight:700, fontSize:'.88rem',
                cursor:'pointer'
              }}>Search Slots Near Me</button>
            </>
          )}

          {state === 'error' && (
            <>
              <div style={{ background:'#fde8e8', border:'1px solid rgba(224,36,36,.2)', borderRadius:'10px', padding:'12px 14px', marginBottom:'14px', fontSize:'.82rem', color:'#e02424' }}>
                {error || 'Location access denied.'}
              </div>
              <p style={{ fontSize:'.82rem', color:'#4a6070', marginBottom:'12px' }}>Enter your coordinates manually:</p>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'8px', marginBottom:'12px' }}>
                <input value={manLat} onChange={e=>setManLat(e.target.value)}
                  placeholder="Latitude (e.g. 13.05)" type="number" step="any"
                  style={{ padding:'9px 11px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.83rem', outline:'none' }}/>
                <input value={manLon} onChange={e=>setManLon(e.target.value)}
                  placeholder="Longitude (e.g. 80.22)" type="number" step="any"
                  style={{ padding:'9px 11px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.83rem', outline:'none' }}/>
              </div>
              <button
                disabled={!manLat || !manLon}
                onClick={() => onManual({ lat: parseFloat(manLat), lon: parseFloat(manLon) })}
                style={{
                  width:'100%', padding:'11px',
                  background: manLat && manLon ? '#00857c' : '#cdd9e2',
                  color:'#fff', border:'none', borderRadius:'10px',
                  fontWeight:700, fontSize:'.88rem',
                  cursor: manLat && manLon ? 'pointer' : 'not-allowed'
                }}>Search with These Coordinates</button>
            </>
          )}

          {state === 'manual' && (
            <>
              <p style={{ fontSize:'.82rem', color:'#4a6070', marginBottom:'12px' }}>Enter your coordinates:</p>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'8px', marginBottom:'12px' }}>
                <input value={manLat} onChange={e=>setManLat(e.target.value)}
                  placeholder="Latitude" type="number" step="any"
                  style={{ padding:'9px 11px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.83rem', outline:'none' }}/>
                <input value={manLon} onChange={e=>setManLon(e.target.value)}
                  placeholder="Longitude" type="number" step="any"
                  style={{ padding:'9px 11px', border:'1px solid #dde4ed', borderRadius:'8px', fontSize:'.83rem', outline:'none' }}/>
              </div>
              <button
                disabled={!manLat || !manLon}
                onClick={() => onManual({ lat: parseFloat(manLat), lon: parseFloat(manLon) })}
                style={{
                  width:'100%', padding:'11px',
                  background: manLat && manLon ? '#00857c' : '#cdd9e2',
                  color:'#fff', border:'none', borderRadius:'10px',
                  fontWeight:700, fontSize:'.88rem',
                  cursor: manLat && manLon ? 'pointer' : 'not-allowed'
                }}>Search Slots Near Me</button>
            </>
          )}

          <button onClick={onClose} style={{
            marginTop:'10px', width:'100%', padding:'9px', background:'none',
            border:'none', color:'#8fa5b3', fontSize:'.8rem', cursor:'pointer'
          }}>Cancel</button>
        </div>
      </div>
    </div>
  );
};

/* ════════════════════════════════════════════
   ROOT APP
   ════════════════════════════════════════════ */
function App() {
  const [sidebarHidden, setSidebarHidden] = useState(false);
  const [messages,      setMessages]      = useState([]);
  const [typing,        setTyping]        = useState(false);
  const [connected,     setConnected]     = useState(false);
  const [connClass,     setConnClass]     = useState('connecting');
  const [connLabel,     setConnLabel]     = useState('Connecting…');
  const [inputVal,      setInputVal]      = useState('');
  const [inspActive,    setInspActive]    = useState(false);
  const [inspData,      setInspData]      = useState(null);
  const [searchMethod,  setSearchMethod]  = useState('—');

  /* GPS modal state */
  const [gpsModal,  setGpsModal]  = useState(false);
  const [gpsState,  setGpsState]  = useState('prompt');   // prompt | loading | success | error | manual
  const [gpsCords,  setGpsCords]  = useState(null);
  const [gpsError,  setGpsError]  = useState('');

  const [userCoords,        setUserCoords]        = useState(null);
  const [activeHospitalIdx, setActiveHospitalIdx] = useState(0);

  /* Booking system state */
  const [bookingHospital,      setBookingHospital]      = useState(null);
  const [bookingConfirmedData, setBookingConfirmedData] = useState(null);

  /* Mobile responsiveness states */
  const [activeTab,     setActiveTab]     = useState('chat'); // chat | map
  const [hasNewResults, setHasNewResults] = useState(false);

  const handleConfirmBooking = (data) => {
    setBookingConfirmedData(data);

    // Trigger backend POST to send booking details email
    fetch('/api/send-booking-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(res => {
      if (res.status === 'success') {
        alert('Vaccination ticket successfully sent to your email ID!');
      } else {
        alert('Booking Confirmed!\n\nEmail dispatch notice:\n' + res.message);
      }
    })
    .catch(err => {
      console.error(err);
      alert('Booking Confirmed!\nEmail system is unreachable.');
    });
  };

  const socketRef  = useRef(null);
  const sidRef     = useRef(null);
  const viewRef    = useRef(null);
  const taRef      = useRef(null);

  /* Auto-scroll */
  useEffect(() => {
    if (viewRef.current) viewRef.current.scrollTop = viewRef.current.scrollHeight;
  }, [messages, typing]);

  /* Socket lifecycle */
  useEffect(() => {
    sidRef.current = getSessionId();

    const setConn = (cls, lbl, ok) => {
      setConnClass(cls); setConnLabel(lbl); setConnected(ok);
    };

    try {
      const sock = io(RASA_URL, {
        transports: ['polling', 'websocket'],
        reconnectionAttempts: 12,
        reconnectionDelay: 2000,
        path: '/socket.io/',
        extraHeaders: { 'Bypass-Tunnel-Reminder': 'true' },
      });
      socketRef.current = sock;

      sock.on('connect', () => {
        setConn('connecting', 'Connecting…', false);
        setTyping(false);
        sock.emit('session_request', { session_id: sidRef.current });
      });

      sock.on('session_confirm', sid => {
        sidRef.current = sid;
        setConn('connected', 'Online', true);
        setMessages(prev =>
          prev.length === 0
            ? [{
                type: 'assistant',
                text: 'Welcome to MAYDEN SMARTHEALTH Vaccine Console. I query live CoWin vaccination databases in real-time.\n\nPlease select a search mode or type your query directly.',
                buttons: [
                  { title: 'Area Pincode',    payload: '/pincode'  },
                  { title: 'District ID',     payload: '/district' },
                  { title: 'GPS Location',    payload: '/location' },
                ],
                time: now(),
              }]
            : [...prev, { type: 'system', text: 'Connection restored', time: now() }]
        );
      });

      sock.on('disconnect', reason => {
        setConn('disconnected', 'Offline', false);
        setTyping(false);
      });

      sock.on('connect_error', () => {
        setConn('disconnected', 'Offline', false);
        setTyping(false);
        setMessages(prev =>
          prev.length === 0
            ? [{
                type: 'assistant',
                text: 'Unable to reach the RASA server on `localhost:5005`.\n\nRun: `rasa run -m models --enable-api --cors "*"`\n\nThe console will retry automatically.',
                time: now(),
              }]
            : prev
        );
      });

      sock.on(BOT_MSG_EVT, data => {
        setTyping(false);
        const text    = data.text?.trim() || null;
        const image   = data.image || null;
        const buttons = data.buttons?.length
          ? data.buttons
          : data.quick_replies?.map(q => ({ title: q.title, payload: q.payload })) || null;

        // Extract user coordinates from bot geocoded header if present
        if (text) {
          const coordsMatch = text.match(/Coordinates:\s*([0-9.-]+)N,\s*([0-9.-]+)E/);
          if (coordsMatch) {
            setUserCoords({ lat: parseFloat(coordsMatch[1]), lon: parseFloat(coordsMatch[2]) });
          } else {
            const gpsMatch = text.match(/Your coordinates:\s*Lat\s*([0-9.-]+),\s*Lon\s*([0-9.-]+)/i);
            if (gpsMatch) {
              setUserCoords({ lat: parseFloat(gpsMatch[1]), lon: parseFloat(gpsMatch[2]) });
            }
          }
        }

        const slotData = parseSlotData(text);
        if (slotData) {
          setInspData(slotData);
          setInspActive(true);
          setActiveHospitalIdx(0); // Reset map highlight to first hospital on new results
          setHasNewResults(true);
          setActiveTab('map'); // Auto switch to map tab on mobile devices
          setMessages(prev => [...prev, {
            type: 'assistant',
            text: `I found **${slotData.facilities.length} vaccination facilit${slotData.facilities.length === 1 ? 'y' : 'ies'}** matching your query. Full details — capacity, dose stock, timings, and age limits — are loaded in the **Live Data Inspector** on the right.`,
            buttons,
            time: now(),
          }]);
        } else {
          if (text || buttons) {
            setMessages(prev => [...prev, { type: 'assistant', text, buttons, time: now() }]);
          }
          if (image) {
            setMessages(prev => [...prev, { type: 'assistant', image, time: now() }]);
          }
        }
      });

    } catch (e) {
      setConn('disconnected', 'Offline', false);
    }

    return () => socketRef.current?.disconnect();
  }, []);

  /* ── GPS helpers ── */
  const openGpsModal = () => {
    setGpsState('prompt');
    setGpsCords(null);
    setGpsError('');
    setGpsModal(true);
  };

  const requestBrowserGps = () => {
    if (!navigator.geolocation) {
      setGpsState('error');
      setGpsError('Geolocation is not supported by your browser. Please enter coordinates manually.');
      return;
    }
    setGpsState('loading');
    navigator.geolocation.getCurrentPosition(
      pos => {
        const coords = { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy };
        setGpsCords(coords);
        setGpsState('success');
      },
      err => {
        const msg = err.code === 1
          ? 'Location permission denied. Please enter coordinates manually.'
          : err.code === 2
          ? 'Position unavailable. Check if location services are enabled.'
          : 'Location request timed out. Please try again or enter manually.';
        setGpsError(msg);
        setGpsState('error');
      },
      { timeout: 10000, maximumAge: 60000, enableHighAccuracy: true }
    );
  };

  const sendGpsCoords = async (coords) => {
    setGpsModal(false);
    setUserCoords(coords);
    const lat = coords.lat.toFixed(5);
    const lon = coords.lon.toFixed(5);
    setSearchMethod('By GPS Coordinates');
    const display = `Search by GPS coordinates: ${lat}, ${lon}`;
    setMessages(prev => [...prev, { type: 'user', text: display, time: now() }]);
    if (!connected) {
      setMessages(prev => [...prev, { type: 'system', text: 'Console is offline', time: now() }]);
      return;
    }
    setTyping(true);

    // Use Rasa REST API to directly set slots and trigger location action,
    // bypassing the multi-turn form which doesn't auto-fill from payload entities.
    try {
      const sid = sidRef.current;
      const baseUrl = RASA_URL;

      // Step 1: Set lattitude slot
      await fetch(`${baseUrl}/conversations/${sid}/tracker/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: 'slot', name: 'lattitude', value: lat }),
      });

      // Step 2: Set longitude slot
      await fetch(`${baseUrl}/conversations/${sid}/tracker/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: 'slot', name: 'longitude', value: lon }),
      });

      // Step 3: Trigger the location action directly via REST API
      const resp = await fetch(`${baseUrl}/conversations/${sid}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'action_location_submit', policy: null, confidence: null }),
      });

      if (resp.ok) {
        const data = await resp.json();
        setTyping(false);
        const responses = data.messages || [];
        responses.forEach(msg => {
          if (msg.text) {
            setMessages(prev => [...prev, { type: 'assistant', text: msg.text, buttons: msg.buttons, time: now() }]);
          }
        });
        if (responses.length === 0) {
          setMessages(prev => [...prev, { type: 'system', text: 'No response from backend. Is the model loaded?', time: now() }]);
        }
      } else {
        // Fallback: use socket emit with the payload (original method)
        setTyping(true);
        const payload = `/location{"lattitude":"${lat}","longitude":"${lon}"}`;
        socketRef.current.emit(USER_MSG_EVT, { message: payload, session_id: sid });
      }
    } catch (err) {
      // Fallback on network error: use socket
      const payload = `/location{"lattitude":"${lat}","longitude":"${lon}"}`;
      socketRef.current.emit(USER_MSG_EVT, { message: payload, session_id: sidRef.current });
    }
  };

  /* Send message */
  const send = useCallback((raw = inputVal) => {
    const text = raw.trim();
    if (!text) return;

    setSidebarHidden(true); // Close drawer overlay on mobile

    // ── Button payload routing ──────────────────────────────────────────
    // RASA buttons send payloads like /pincode, /district, /location
    // These are intent shortcuts — handle them before anything else.
    if (text === '/location' || text === 'By Location(lat-lon)') {
      openGpsModal();
      return;
    }

    // Map slash-intent payloads to human-readable chat labels
    const PAYLOAD_LABELS = {
      '/pincode':  'Search by Pincode',
      '/district': 'Search by District ID',
      '/restart':  'Restart conversation',
    };
    const displayText = PAYLOAD_LABELS[text] || text;

    // Track search mode for inspector panel
    if (text === '/pincode'  || /pincode/i.test(text))   setSearchMethod('By Pincode');
    else if (text === '/district' || /district/i.test(text)) setSearchMethod('By District ID');
    else if (/location|lat|lon/i.test(text))              setSearchMethod('By GPS Coordinates');

    // Show the human-readable label in the chat feed
    setMessages(prev => [...prev, { type: 'user', text: displayText, time: now() }]);
    setInputVal('');
    if (taRef.current) { taRef.current.style.height = 'auto'; }

    if (!connected) {
      setMessages(prev => [...prev, { type: 'system', text: 'Console is offline', time: now() }]);
      return;
    }

    // Always send the original payload/text to RASA so slash-intents work
    setTyping(true);
    socketRef.current.emit('user_uttered', { message: text, session_id: sidRef.current });
  }, [inputVal, connected]);

  /* Reset */
  const reset = () => {
    setMessages([{ type: 'system', text: 'Conversation reset', time: now() }]);
    setInspActive(false);
    setInspData(null);
    setSearchMethod('—');
  };

  const newSession = () => {
    setMessages([{ type: 'system', text: 'New session started', time: now() }]);
    setInspActive(false);
    setInspData(null);
    setSearchMethod('—');
    if (connected) socketRef.current.emit(USER_MSG_EVT, { message: '/restart', session_id: sidRef.current });
  };

  const handleTA = e => {
    setInputVal(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px';
  };

  const hasMessages = messages.length > 0;

  return (
    <Fragment>
    <GpsModal
      state={gpsModal ? gpsState : null}
      coords={gpsCords}
      error={gpsError}
      onAllow={requestBrowserGps}
      onManual={(c) => c ? sendGpsCoords(c) : setGpsState('manual')}
      onClose={() => setGpsModal(false)}
    />
    <BookingModal
      hospital={bookingHospital}
      confirmedData={bookingConfirmedData}
      onClose={() => { setBookingHospital(null); setBookingConfirmedData(null); }}
      onConfirm={handleConfirmBooking}
    />
    <div className={`hospital-app ${sidebarHidden ? 'sidebar-hidden' : ''} ${activeTab === 'chat' ? 'show-chat' : 'show-map'}`}>

      {/* Backdrop overlay for closing sidebar on mobile */}
      {!sidebarHidden && (
        <div className="sidebar-backdrop" onClick={() => setSidebarHidden(true)} />
      )}

      {/* SIDEBAR */}
      <Sidebar connClass={connClass} connLabel={connLabel} onMode={send} />

      {/* CHAT PANEL */}
      <main className="chat-panel">

        {/* ECG Header */}
        <header className="chat-header">
          <div className="header-left">
            <button className="toggle-btn" onClick={() => setSidebarHidden(p => !p)} title="Toggle sidebar">
              <MenuIcon />
            </button>
            <div className="header-info">
              <div className="header-title">Vaccine Slot Assistant</div>
              <div className="header-sub">Hospital Intelligence Engine</div>
            </div>
          </div>
          <div className="header-right">
            <button className="hdr-btn" onClick={reset}>
              <TrashIcon /> <span className="hdr-btn-text">Reset Feed</span>
            </button>
            <button className="hdr-btn" onClick={newSession} style={{ marginLeft: '6px' }}>
              <PlusIcon /> <span className="hdr-btn-text">New Session</span>
            </button>
          </div>
          <EcgWave />
        </header>

        {/* Mobile Tab Switcher */}
        <div className="mobile-tabs">
          <button 
            className={`mobile-tab-btn ${activeTab === 'chat' ? 'active' : ''}`} 
            onClick={() => setActiveTab('chat')}
          >
            Chat Assistant
          </button>
          <button 
            className={`mobile-tab-btn ${activeTab === 'map' ? 'active' : ''} ${hasNewResults ? 'has-badge' : ''}`} 
            onClick={() => { setActiveTab('map'); setHasNewResults(false); }}
          >
            Map & Results
          </button>
        </div>

        {/* Viewport */}
        <div className="chat-viewport" ref={viewRef}>
          {!hasMessages ? (
            <WelcomeScreen onMode={send} />
          ) : (
            <div className="messages-list">
              {messages.map((m, i) => (
                <MessageRow key={i} msg={m} onChoice={send} />
              ))}
            </div>
          )}

          {typing && (
            <div className="typing-row">
              <div className="msg-avatar bot-av">AI</div>
              <div className="typing-dots">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <footer className="input-footer">
          <div className="input-inner">
            <div className="input-box">
              <textarea
                ref={taRef}
                className="chat-textarea"
                rows={1}
                value={inputVal}
                onChange={handleTA}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                placeholder="Type a pincode, district ID, or ask a general query…"
              />
              <button
                className="send-btn"
                onClick={() => send()}
                disabled={!connected || !inputVal.trim()}
              >
                <SendIcon />
              </button>
            </div>
            <div className="input-note">
              Live CoWin data feed · No personal data is stored or logged.
            </div>
          </div>
        </footer>
      </main>

      {/* DATA INSPECTOR */}
      <DataInspector
        active={inspActive}
        data={inspData}
        searchMethod={searchMethod}
        userCoords={userCoords}
        activeHospitalIdx={activeHospitalIdx}
        setActiveHospitalIdx={setActiveHospitalIdx}
        onBook={setBookingHospital}
      />

    </div>
    </Fragment>
  );
}

/* Mount */
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
