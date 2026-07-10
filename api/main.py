"""
LifeEazy Vaccine Bot — main.py
Real Data Pipeline:
  CoWin API (Real-time slots)  →  Public immunization sessions by Pincode/District
  Nominatim (Geocode fallback) →  Coordinates lookup
  Overpass (OSM fallback)      →  Real healthcare facilities when no active vaccine sessions
"""

import math
import time
import requests
import datetime

# ── HTTP session shared across calls ──────────────────────────────────────────
_session = requests.Session()
# Use a browser User-Agent to prevent CoWin from blocking requests
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en",
})

# ── Tamil Nadu district ID → name (for district search) ──────────────────────
TN_DISTRICT_MAP = {
    "573": "Chennai",        "574": "Kanchipuram",   "575": "Tiruvallur",
    "576": "Vellore",        "577": "Tiruvannamalai", "578": "Cuddalore",
    "579": "Villupuram",     "580": "Salem",          "581": "Dharmapuri",
    "582": "Krishnagiri",    "583": "Namakkal",       "584": "Erode",
    "585": "Coimbatore",     "586": "Nilgiris",       "587": "Tiruppur",
    "588": "Madurai",        "589": "Dindigul",       "590": "Theni",
    "591": "Virudhunagar",   "592": "Ramanathapuram", "593": "Sivaganga",
    "594": "Tirunelveli",    "595": "Thoothukudi",    "596": "Kanniyakumari",
    "597": "Karur",          "598": "Tiruchirappalli","599": "Perambalur",
    "600": "Ariyalur",       "601": "Thanjavur",      "602": "Nagapattinam",
    "603": "Tiruvarur",      "604": "Pudukkottai",    "605": "Chengalpattu",
}

# ── Haversine distance (km) ───────────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2):
    try:
        R = 6371
        p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
        dp = math.radians(float(lat2) - float(lat1))
        dl = math.radians(float(lon2) - float(lon1))
        a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    except Exception:
        return 9999.0


# ══════════════════════════════════════════════════════════════════════════════
# NOMINATIM GEOLOCATION UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
# ── Chennai Precise Pincodes Dictionary ─────────────────────────────────────────
CHENNAI_PINCODES = {
    "600001": (13.1000, 80.2800, "George Town, Chennai, Tamil Nadu, India"),
    "600002": (13.0600, 80.2600, "Mount Road, Chennai, Tamil Nadu, India"),
    "600003": (13.0800, 80.2700, "Park Town, Chennai, Tamil Nadu, India"),
    "600004": (13.0330, 80.2680, "Mylapore, Chennai, Tamil Nadu, India"),
    "600005": (13.0600, 80.2770, "Triplicane, Chennai, Tamil Nadu, India"),
    "600006": (13.0570, 80.2500, "Greams Road, Chennai, Tamil Nadu, India"),
    "600007": (13.0880, 80.2580, "Vepery, Chennai, Tamil Nadu, India"),
    "600008": (13.0780, 80.2600, "Egmore, Chennai, Tamil Nadu, India"),
    "600010": (13.0830, 80.2400, "Kilpauk, Chennai, Tamil Nadu, India"),
    "600012": (13.0970, 80.2510, "Perambur Barracks Road, Chennai, Tamil Nadu, India"),
    "600014": (13.0530, 80.2600, "Royapettah, Chennai, Tamil Nadu, India"),
    "600015": (13.0180, 80.2290, "Saidapet, Chennai, Tamil Nadu, India"),
    "600017": (13.0400, 80.2330, "T. Nagar, Chennai, Tamil Nadu, India"),
    "600018": (13.0330, 80.2500, "Alwarpet, Chennai, Tamil Nadu, India"),
    "600020": (13.0060, 80.2570, "Adyar, Chennai, Tamil Nadu, India"),
    "600024": (13.0500, 80.2200, "Kodambakkam, Chennai, Tamil Nadu, India"),
    "600028": (13.0200, 80.2600, "Raja Annamalaipuram, Chennai, Tamil Nadu, India"),
    "600034": (13.0600, 80.2400, "Nungambakkam, Chennai, Tamil Nadu, India"),
    "600040": (13.0850, 80.2100, "Anna Nagar, Chennai, Tamil Nadu, India"),
    "600041": (12.9800, 80.2600, "Thiruvanmiyur, Chennai, Tamil Nadu, India"),
    "600042": (12.9800, 80.2200, "Velachery, Chennai, Tamil Nadu, India"),
    "600096": (12.9600, 80.2400, "Perungudi, Chennai, Tamil Nadu, India"),
    "600097": (12.9400, 80.2300, "Thoraipakkam, Chennai, Tamil Nadu, India"),
    "600100": (12.9100, 80.1900, "Medavakkam, Chennai, Tamil Nadu, India"),
}

def _geocode_pincode(pincode: str):
    pincode = str(pincode).strip()
    if pincode in CHENNAI_PINCODES:
        return CHENNAI_PINCODES[pincode]

    urls = [
        f"https://nominatim.openstreetmap.org/search"
        f"?q={pincode}+Chennai+Tamil+Nadu+India&format=json&limit=1&addressdetails=1",
        f"https://nominatim.openstreetmap.org/search"
        f"?postalcode={pincode}&country=India&format=json&limit=1&addressdetails=1",
        f"https://nominatim.openstreetmap.org/search"
        f"?q={pincode}+India&format=json&limit=1&addressdetails=1",
    ]
    for url in urls:
        try:
            time.sleep(1.1)
            r = _session.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", "")
        except Exception:
            continue
    return None

def _geocode_place(place: str, country: str = "India"):
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={requests.utils.quote(place)}+{country}&format=json&limit=1"
    )
    try:
        time.sleep(1.1)
        r = _session.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", "")
    except Exception:
        pass
    return None

def _reverse_geocode_pincode(lat: float, lon: float):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
    try:
        time.sleep(1.1)
        r = _session.get(url, timeout=8)
        if r.status_code == 200:
            addr = r.json().get("address", {})
            return addr.get("postcode")
    except Exception:
        pass
    return None

def _normalize_pincode(p):
    if not p:
        return ""
    return "".join(c for c in str(p) if c.isdigit())

def _normalize_date(date_str):
    if not date_str:
        return datetime.datetime.now().strftime("%d-%m-%Y")
    date_str = str(date_str).strip()
    parts = date_str.split("-")
    if len(parts) == 3 and len(parts[0]) <= 2 and len(parts[1]) <= 2 and len(parts[2]) == 4:
        return f"{int(parts[0]):02d}-{int(parts[1]):02d}-{parts[2]}"
    
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%d-%m-%Y")
        except Exception:
            continue
    return datetime.datetime.now().strftime("%d-%m-%Y")


# ══════════════════════════════════════════════════════════════════════════════
# COWIN LIVE API DATA SOURCE
# ══════════════════════════════════════════════════════════════════════════════
def _cowin_by_pincode(pincode: str, date: str):
    url = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode={pincode}&date={date}"
    try:
        r = _session.get(url, timeout=8)
        if r.status_code == 200:
            return r.json().get("sessions", [])
    except Exception:
        pass
    return []

def _cowin_by_district(district_id: str, date: str):
    url = f"https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id={district_id}&date={date}"
    try:
        r = _session.get(url, timeout=8)
        if r.status_code == 200:
            return r.json().get("sessions", [])
    except Exception:
        pass
    return []


# ── Chennai Hand-Curated High-Quality Hospitals Database ─────────────────────
LOCAL_HOSPITALS = [
    {
        "name": "Government Stanley Medical College Hospital",
        "address": "Stanley Hospital Rd, Old Jail Rd, Royapuram, Chennai",
        "pincode": "600001",
        "kind": "Government Hospital",
        "phone": "+91-44-25281351",
        "website": "http://www.stanleymc.ac.in",
        "lat": 13.10672, "lon": 80.28415,
    },
    {
        "name": "Rajiv Gandhi Government General Hospital (RGGGH)",
        "address": "E.V.R. Periyar Salai, Park Town, Chennai",
        "pincode": "600003",
        "kind": "Government General Hospital",
        "phone": "+91-44-25305000",
        "website": "http://www.mmc.ac.in",
        "lat": 13.07921, "lon": 80.27643,
    },
    {
        "name": "Apollo Hospitals Greams Road",
        "address": "21, Greams Lane, Off Greams Road, Thousand Lights, Chennai",
        "pincode": "600006",
        "kind": "Multi-Specialty Private Hospital",
        "phone": "+91-44-28290200",
        "website": "https://www.apollohospitals.com",
        "lat": 13.06121, "lon": 80.25272,
    },
    {
        "name": "Apollo Children's Hospital Thousand Lights",
        "address": "15, Shafee Mohammed Road, Thousand Lights West, Chennai",
        "pincode": "600006",
        "kind": "Pediatric Clinic / Hospital",
        "phone": "+91-44-28294444",
        "website": "https://chennai.apollohospitals.com",
        "lat": 13.06341, "lon": 80.25432,
    },
    {
        "name": "K.J. Hospital & Postgraduate Aesthetic Surgery Center",
        "address": "182, Poonamallee High Rd, Kilpauk, Chennai",
        "pincode": "600010",
        "kind": "Specialty Hospital",
        "phone": "+91-44-26411500",
        "website": "http://www.kjhospital.com",
        "lat": 13.07843, "lon": 80.24584,
    },
    {
        "name": "Dr. U. Mohan Rao Memorial Hospital",
        "address": "3/2, 2nd Cross St, CIT Colony, Mylapore, Chennai",
        "pincode": "600004",
        "kind": "Private Clinic / Hospital",
        "phone": "+91-44-24990550",
        "website": "https://dumr.org",
        "lat": 13.03365, "lon": 80.25821,
    },
    {
        "name": "Fortis Malar Hospital Adyar",
        "address": "52, 1st Main Rd, Gandhi Nagar, Adyar, Chennai",
        "pincode": "600020",
        "kind": "Super Specialty Hospital",
        "phone": "+91-44-42424242",
        "website": "https://www.fortismalar.com",
        "lat": 13.00192, "lon": 80.25642,
    },
    {
        "name": "SIMS Hospital Vadapalani",
        "address": "1, Jawaharlal Nehru Salai, Vadapalani, Chennai",
        "pincode": "600026",
        "kind": "Multi-Specialty Hospital",
        "phone": "+91-44-20002001",
        "website": "https://www.simshospitals.com",
        "lat": 13.05342, "lon": 80.21245,
    },
    {
        "name": "Venkataeswara Hospitals Mylapore",
        "address": "36-A, Chamiers Rd, Nandanam, Chennai",
        "pincode": "600035",
        "kind": "Cardiac Care Hospital",
        "phone": "+91-44-45111111",
        "website": "http://www.venkataeswarahospitals.com",
        "lat": 13.02871, "lon": 80.24352,
    },
    {
        "name": "Billroth Hospitals Shenoy Nagar",
        "address": "43, Lakshmi Talkies Rd, Shenoy Nagar, Chennai",
        "pincode": "600030",
        "kind": "Multi-Specialty Private Hospital",
        "phone": "+91-44-26641500",
        "website": "https://billrothhospitals.com",
        "lat": 13.09282, "lon": 80.23371,
    },
    {
        "name": "Kauvery Hospital Anna Nagar",
        "address": "199, Jawaharlal Nehru Salai, Anna Nagar, Chennai",
        "pincode": "600040",
        "kind": "Super Specialty Hospital",
        "phone": "+91-44-40006000",
        "website": "https://www.kauveryhospital.com",
        "lat": 13.08795, "lon": 80.21123,
    },
    {
        "name": "Sooriya Hospital Vadapalani",
        "address": "1, 100 Feet Rd, Vadapalani, Chennai",
        "pincode": "600026",
        "kind": "General Hospital",
        "phone": "+91-44-24891640",
        "website": "http://www.sooriyahospital.com",
        "lat": 13.05191, "lon": 80.21052,
    },
    {
        "name": "Fortis Hospital Vadapalani",
        "address": "100 Feet Road, Vadapalani, Chennai",
        "pincode": "600026",
        "kind": "Super Specialty Hospital",
        "phone": "+91-44-43434343",
        "website": "https://www.fortishealthcare.com",
        "lat": 13.05423, "lon": 80.21182,
    },
    {
        "name": "MGM Healthcare Aminjikarai",
        "address": "72, Nelson Manickam Rd, Aminjikarai, Chennai",
        "pincode": "600029",
        "kind": "Super Specialty Hospital",
        "phone": "+91-44-45242424",
        "website": "https://mgmhealthcare.in",
        "lat": 13.06963, "lon": 80.21915,
    },
    {
        "name": "Sundaram Medical Foundation (SMF) Anna Nagar",
        "address": "9C, 4th Avenue, Shanthi Colony, Anna Nagar, Chennai",
        "pincode": "600040",
        "kind": "Community General Hospital",
        "phone": "+91-44-26268844",
        "website": "http://www.smf-hospital.org",
        "lat": 13.08412, "lon": 80.21634,
    },
    {
        "name": "Gleneagles Global Health City Perumbakkam",
        "address": "439, Cheran Nagar, Perumbakkam, Chennai",
        "pincode": "600100",
        "kind": "Organ Transplant Specialty Hospital",
        "phone": "+91-44-44777000",
        "website": "https://www.gleneaglesglobalhealthcity.in",
        "lat": 12.91612, "lon": 80.21614,
    },
    {
        "name": "Sri Ramachandra Hospital Porur",
        "address": "1, Ramachandra Nagar, Porur, Chennai",
        "pincode": "600116",
        "kind": "Teaching Hospital & Research Center",
        "phone": "+91-44-45928500",
        "website": "https://www.sriramachandra.edu.in",
        "lat": 13.03541, "lon": 80.15743,
    },
    {
        "name": "Tambaram Government Hospital of Thoracic Medicine",
        "address": "GST Road, Sanatorium, Tambaram East, Chennai",
        "pincode": "600047",
        "kind": "Government Specialty Hospital",
        "phone": "+91-44-22418431",
        "website": "http://www.ghttambaram.org",
        "lat": 12.92874, "lon": 80.11921,
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# FALLBACK: OVERPASS (OSM)
# ══════════════════════════════════════════════════════════════════════════════
def _overpass_hospitals(lat: float, lon: float, radius_m: int = 5000, target_pincode: str = None):
    """
    Queries OpenStreetMap via Overpass API for real healthcare facilities.
    Merges results with local database, deduplicates, and sorts by proximity.
    """
    query = f"""
[out:json][timeout:30];
(
  node["amenity"="hospital"](around:{radius_m},{lat},{lon});
  way["amenity"="hospital"](around:{radius_m},{lat},{lon});
  node["amenity"="clinic"](around:{radius_m},{lat},{lon});
  way["amenity"="clinic"](around:{radius_m},{lat},{lon});
  node["amenity"="doctors"](around:{radius_m},{lat},{lon});
  node["healthcare"="hospital"](around:{radius_m},{lat},{lon});
  node["healthcare"="clinic"](around:{radius_m},{lat},{lon});
);
out body center;
""".strip()

    osm_facilities = []
    
    for endpoint in ["https://overpass-api.de/api/interpreter", "https://lz4.overpass-api.de/api/interpreter"]:
        try:
            r = _session.post(endpoint, data=query, timeout=12)
            if r.status_code == 200:
                elements = r.json().get("elements", [])
                for el in elements:
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("name:en") or tags.get("operator")
                    if not name:
                        continue

                    if el["type"] == "node":
                        elat, elon = el.get("lat", lat), el.get("lon", lon)
                    else:
                        center = el.get("center", {})
                        elat = center.get("lat", lat)
                        elon = center.get("lon", lon)

                    addr_parts = [
                        tags.get("addr:housenumber", ""),
                        tags.get("addr:street", ""),
                        tags.get("addr:suburb", ""),
                        tags.get("addr:city", ""),
                        tags.get("addr:postcode", ""),
                    ]
                    address = ", ".join(p for p in addr_parts if p) or tags.get("addr:full", "")
                    phone = tags.get("phone") or tags.get("contact:phone", "")
                    website = tags.get("website") or tags.get("contact:website", "")
                    kind = tags.get("amenity") or tags.get("healthcare", "hospital")
                    
                    dist_km = _haversine(lat, lon, elat, elon)
                    
                    osm_facilities.append({
                        "name": name,
                        "address": address or "Chennai, Tamil Nadu",
                        "pincode": tags.get("addr:postcode", ""),
                        "kind": kind.replace("_", " ").title(),
                        "phone": phone,
                        "website": website,
                        "lat": elat,
                        "lon": elon,
                        "dist_km": round(dist_km, 2),
                        "available_capacity_dose1": 0,
                        "available_capacity_dose2": 0,
                        "available_capacity": 0,
                        "min_age_limit": "18+ (OPD)",
                        "slots": ["09:00 AM - 12:00 PM (OPD)", "02:00 PM - 05:00 PM (OPD)"],
                        "state_name": "Tamil Nadu",
                        "district_name": tags.get("addr:city", "Chennai"),
                    })
                break
        except Exception:
            continue

    # Merge with local database
    local_facilities = []
    for h in LOCAL_HOSPITALS:
        dist_km = _haversine(lat, lon, h["lat"], h["lon"])
        if dist_km <= 15.0:
            local_facilities.append({
                "name": h["name"],
                "address": h["address"],
                "pincode": h["pincode"],
                "kind": h["kind"],
                "phone": h["phone"],
                "website": h["website"],
                "lat": h["lat"],
                "lon": h["lon"],
                "dist_km": round(dist_km, 2),
                "available_capacity_dose1": 0,
                "available_capacity_dose2": 0,
                "available_capacity": 0,
                "min_age_limit": "18+ (OPD)",
                "slots": ["09:00 AM - 12:00 PM (OPD)", "02:00 PM - 05:00 PM (OPD)"],
                "state_name": "Tamil Nadu",
                "district_name": "Chennai",
            })

    # De-duplicate
    seen_names = set()
    unique_facilities = []
    for f in (osm_facilities + local_facilities):
        normalized = "".join(c for c in f["name"].lower() if c.isalnum())
        if normalized not in seen_names:
            seen_names.add(normalized)
            unique_facilities.append(f)

    # Sort
    target_pin_norm = _normalize_pincode(target_pincode) if target_pincode else None
    if target_pin_norm:
        def sort_key(x):
            fac_pin_norm = _normalize_pincode(x.get("pincode"))
            if fac_pin_norm == target_pin_norm:
                prio = 0
            elif not fac_pin_norm or fac_pin_norm == "na":
                prio = 1
            else:
                prio = 2
            return (prio, x["dist_km"])
        unique_facilities.sort(key=sort_key)
    else:
        unique_facilities.sort(key=lambda x: x["dist_km"])
    return unique_facilities[:8]


# ══════════════════════════════════════════════════════════════════════════════
# FORMATTER — Converts facility list → RASA text response
# ══════════════════════════════════════════════════════════════════════════════
def _format(facilities, header=""):
    if not facilities:
        return (
            header +
            "No active sessions / healthcare centres found nearby.\n"
            "Try checking the pincode or try another date."
        )

    out = header
    for f in facilities:
        out += "******************************\n"
        out += f"Hospital Name: {f['name']}\n"
        out += (
            f"Address: {f['address']}\n"
            f"Pincode: {f['pincode'] or 'N/A'}\n"
            f"Type: {f['kind']}\n"
            f"available_capacity_dose1 : {f['available_capacity_dose1']}\n"
            f"available_capacity_dose2 : {f['available_capacity_dose2']}\n"
            f"available_capacity : {f['available_capacity']}\n"
            f"min_age_limit: {f['min_age_limit']}\n"
            f"Time Slots: {', '.join(f['slots'])}\n"
            f"Distance: {f['dist_km']} km\n"
            + (f"Phone: {f['phone']}\n" if f.get('phone')    else "")
            + (f"Web:   {f['website']}\n" if f.get('website')  else "")
            + f"state_name: {f['state_name']}\n"
            f"district_name: {f['district_name']}\n"
            f"latitude: {f['lat']}\n"
            f"longitude: {f['lon']}\n"
        )
    out += "******************************\n"
    return out


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC FUNCTIONS (called from actions.py)
# ══════════════════════════════════════════════════════════════════════════════

def Dose_Availability_Pincode(pincode, date):
    pincode = str(pincode).strip()
    norm_date = _normalize_date(date)

    # 1. Fetch real-time slots from CoWin API
    cowin_sessions = _cowin_by_pincode(pincode, norm_date)
    
    geo = _geocode_pincode(pincode)
    lat, lon, place_name = geo if geo else (13.0827, 80.2707, "Chennai, TN")
    short_place = place_name.split(",")[0] if place_name else pincode

    facilities = []
    if cowin_sessions:
        for s in cowin_sessions:
            facilities.append(_map_cowin_session(s, lat, lon))
        # Sort CoWin sessions by distance
        facilities.sort(key=lambda x: x["dist_km"])
        header = (
            f"Live CoWin Vaccine Slots near Pincode {pincode} ({short_place})\n"
            f"Source: Real-time CoWin Portal  |  Date: {norm_date}\n"
        )
    else:
        # 2. Fall back to OSM healthcare centers if no active vaccine sessions
        osm_hospitals = _overpass_hospitals(lat, lon, radius_m=6000, target_pincode=pincode)
        if not osm_hospitals:
            osm_hospitals = _overpass_hospitals(lat, lon, radius_m=15000, target_pincode=pincode)
        facilities = osm_hospitals
        header = (
            f"No active CoWin immunizations near Pincode {pincode} today.\n"
            f"Showing general medical centers within range:\n"
        )

    return _format(facilities[:8], header=header)


def Dose_Availability_District(district_id, date):
    district_id = str(district_id).strip()
    norm_date = _normalize_date(date)
    district_name = TN_DISTRICT_MAP.get(district_id, "")

    if not district_name:
        return (
            f"Unknown district ID '{district_id}'.\n"
            "Tamil Nadu district IDs: 573 (Chennai), 574 (Kanchipuram), "
            "575 (Tiruvallur), 585 (Coimbatore), 588 (Madurai).\n"
        )

    # 1. Fetch real-time slots from CoWin API
    cowin_sessions = _cowin_by_district(district_id, norm_date)

    geo = _geocode_place(f"{district_name}, Tamil Nadu")
    lat, lon, _ = geo if geo else (13.0827, 80.2707, "Chennai, TN")

    facilities = []
    if cowin_sessions:
        for s in cowin_sessions:
            facilities.append(_map_cowin_session(s, lat, lon))
        facilities.sort(key=lambda x: x["dist_km"])
        header = (
            f"Live CoWin Vaccine Slots in {district_name} District\n"
            f"Source: Real-time CoWin Portal  |  Date: {norm_date}\n"
        )
    else:
        # 2. Fall back to OSM healthcare centers
        osm_hospitals = _overpass_hospitals(lat, lon, radius_m=10000)
        if not osm_hospitals:
            osm_hospitals = _overpass_hospitals(lat, lon, radius_m=20000)
        facilities = osm_hospitals
        header = (
            f"No active CoWin immunizations in {district_name} District today.\n"
            f"Showing general medical centers:\n"
        )

    return _format(facilities[:8], header=header)


def Dose_Availability_Lon_Lat(lattitude, longitude):
    try:
        lat = float(str(lattitude).strip())
        lon = float(str(longitude).strip())
    except (TypeError, ValueError):
        return "Invalid coordinates. Please enter valid numbers."

    # Search CoWin by reverse-geocoding coordinates to a pincode
    pincode = _reverse_geocode_pincode(lat, lon)
    cowin_sessions = []
    norm_date = datetime.datetime.now().strftime("%d-%m-%Y")
    
    if pincode:
        cowin_sessions = _cowin_by_pincode(pincode, norm_date)

    facilities = []
    if cowin_sessions:
        for s in cowin_sessions:
            facilities.append(_map_cowin_session(s, lat, lon))
        facilities.sort(key=lambda x: x["dist_km"])
        header = (
            f"Live CoWin Vaccine Slots near your GPS location\n"
            f"Source: Real-time CoWin Portal  |  Coordinates: {lat:.4f}N, {lon:.4f}E\n"
        )
    else:
        osm_hospitals = _overpass_hospitals(lat, lon, radius_m=5000)
        if not osm_hospitals:
            osm_hospitals = _overpass_hospitals(lat, lon, radius_m=12000)
        facilities = osm_hospitals
        header = (
            f"No active CoWin immunizations at your GPS coordinates.\n"
            f"Coordinates: {lat:.4f}N, {lon:.4f}E  |  Search radius: 5 km\n"
        )

    return _format(facilities[:8], header=header)


def _map_cowin_session(s, center_lat, center_lon):
    flat = s.get("lat")
    flon = s.get("long")
    
    use_fallback = False
    try:
        if not flat or not flon or float(flat) == 0.0 or float(flon) == 0.0:
            use_fallback = True
        else:
            # Check if CoWin's own coordinates are way off (e.g. > 15 km away from search target)
            dist_check = _haversine(center_lat, center_lon, flat, flon)
            if dist_check > 15.0:
                use_fallback = True
    except Exception:
        use_fallback = True

    if use_fallback:
        # Fallback: reverse lookup center coordinates
        geo = _geocode_place(f"{s.get('name')}, {s.get('pincode')}")
        if geo:
            flat, flon, _ = geo
            # Double check if Nominatim geocoded coordinates are also way off
            if _haversine(center_lat, center_lon, flat, flon) > 15.0:
                flat, flon = None, None
        else:
            flat, flon = None, None

    # If geocoding failed or was also way off, fallback to center coordinates with small random jitter
    if not flat or not flon:
        import random
        # Jitter of approx 0.005 degrees (approx 500 meters)
        flat = float(center_lat) + random.uniform(-0.005, 0.005)
        flon = float(center_lon) + random.uniform(-0.005, 0.005)

    dist_km = _haversine(center_lat, center_lon, flat, flon)
    return {
        "name": s.get("name") or "Vaccination Centre",
        "address": s.get("address") or "CoWin Location",
        "pincode": str(s.get("pincode") or ""),
        "kind": f"{s.get('vaccine', 'Vaccine')} ({s.get('fee_type', 'Free')})",
        "phone": "",
        "website": "",
        "lat": float(flat),
        "lon": float(flon),
        "dist_km": round(dist_km, 2),
        "available_capacity_dose1": s.get("available_capacity_dose1", 0),
        "available_capacity_dose2": s.get("available_capacity_dose2", 0),
        "available_capacity": s.get("available_capacity", 0),
        "min_age_limit": str(s.get("min_age_limit", "18")) + "+",
        "slots": s.get("slots") or ["09:00 AM - 05:00 PM"],
        "state_name": s.get("state_name") or "Tamil Nadu",
        "district_name": s.get("district_name") or "Chennai",
    }


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL (unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def send_email(email, message):
    import urllib.request
    import json
    import os

    username = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")

    if not username or not password:
        creds_path = "creds.txt"
        if not os.path.exists(creds_path):
            creds_path = os.path.join(os.path.dirname(__file__), "creds.txt")
        if os.path.exists(creds_path):
            with open(creds_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 2:
                username = lines[0]
                password = lines[1]
            elif len(lines) == 1:
                username = "innovateyourself2build@gmail.com"
                password = lines[0]

    try:
        url = "https://frontend-wine-seven-77.vercel.app/api/send-booking-email"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "email": email,
            "message": message,
            "name": "Information Request",
            "age": "18",
            "vaccine": "CoWin",
            "dose": "Live Data",
            "timeSlot": "09:00 AM - 05:00 PM",
            "refCode": "MAYDEN-SLOTS",
            "hospitalName": message,
            "hospitalAddress": "Chennai, Tamil Nadu",
            "email_user": username,
            "email_pass": password
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            if res_json.get("status") == "success":
                return "success"
            else:
                return f"Failed to send email. Error: {res_json.get('message')}"
    except Exception as e:
        return f"Failed to send email. Error: {str(e)}"