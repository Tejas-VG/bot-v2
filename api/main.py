"""
LifeEazy Vaccine Bot — main.py
Real Data Pipeline:
  Pincode  →  Nominatim (geocode)  →  Overpass (real hospitals)
  District →  Nominatim (geocode)  →  Overpass (real hospitals)
  Lat/Lon  →  Overpass (real hospitals, sorted by distance)
  Groq     →  AI fallback (already in actions.py)
"""

import math
import time
import requests

# ── HTTP session shared across calls ──────────────────────────────────────────
_session = requests.Session()
_session.headers.update({
    "User-Agent": "MaydenSmartHealthBot/2.0 (contact: admin@maydensmarthealth.com)",
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
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — NOMINATIM: Pincode / place name → (lat, lon)
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
    """
    Returns (lat, lon, display_name) or None.
    First checks our precise local database for Chennai coordinates, then falls back to API.
    """
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
            time.sleep(1.1)          # Nominatim: max 1 req/sec
            r = _session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", "")
        except Exception:
            continue
    return None


def _geocode_place(place: str, country: str = "India"):
    """
    Generic geocode for a city / district name.
    Returns (lat, lon, display_name) or None.
    """
    url = (
        f"https://nominatim.openstreetmap.org/search"
        f"?q={requests.utils.quote(place)}+{country}&format=json&limit=1"
    )
    try:
        time.sleep(1.1)
        r = _session.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", "")
    except Exception:
        pass
    return None


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
# STEP 2 — OVERPASS: (lat, lon) → real hospitals/clinics within radius_m metres
# ══════════════════════════════════════════════════════════════════════════════
def _overpass_hospitals(lat: float, lon: float, radius_m: int = 5000):
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
    
    # Try fetching from OSM Overpass with multiple backups
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
                        "available_capacity_dose1": "Contact centre",
                        "available_capacity_dose2": "Contact centre",
                        "available_capacity": "Call to confirm",
                        "min_age_limit": 18,
                        "slots": ["09:00 AM - 12:00 PM", "02:00 PM - 05:00 PM"],
                        "state_name": "Tamil Nadu",
                        "district_name": tags.get("addr:city", "Chennai"),
                    })
                break  # Successful fetch, stop trying endpoints
        except Exception:
            continue

    # Merge with local high-quality database (filtering to maximum 15km vicinity)
    local_facilities = []
    for h in LOCAL_HOSPITALS:
        dist_km = _haversine(lat, lon, h["lat"], h["lon"])
        if dist_km <= 15.0:  # within 15 km
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
                "available_capacity_dose1": "Contact centre",
                "available_capacity_dose2": "Contact centre",
                "available_capacity": "Call to confirm",
                "min_age_limit": 18,
                "slots": ["09:00 AM - 12:00 PM", "02:00 PM - 05:00 PM"],
                "state_name": "Tamil Nadu",
                "district_name": "Chennai",
            })

    # De-duplicate by normalized alphanumeric name
    seen_names = set()
    unique_facilities = []
    for f in (osm_facilities + local_facilities):
        normalized = "".join(c for c in f["name"].lower() if c.isalnum())
        if normalized not in seen_names:
            seen_names.add(normalized)
            unique_facilities.append(f)

    # Sort all by actual geocoded distance (closest first)
    unique_facilities.sort(key=lambda x: x["dist_km"])
    return unique_facilities[:8]


# ══════════════════════════════════════════════════════════════════════════════
# FORMATTER — Converts facility list → RASA text response
# ══════════════════════════════════════════════════════════════════════════════
def _format(facilities, header=""):
    if not facilities:
        return (
            header +
            "No vaccination / healthcare centres found nearby.\n"
            "Try increasing the search area or check the pincode."
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
            + (f"Phone: {f['phone']}\n" if f["phone"]    else "")
            + (f"Web:   {f['website']}\n" if f["website"] else "")
            + f"state_name: {f['state_name']}\n"
            f"district_name: {f['district_name']}\n"
        )
    out += "******************************\n"
    return out


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC FUNCTIONS  (called from actions.py — signatures unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def Dose_Availability_Pincode(pincode, date):
    """
    Pipeline:
      1. Nominatim  →  pincode → (lat, lon)
      2. Overpass   →  (lat, lon) → real hospitals within 5 km
    """
    pincode = str(pincode).strip()

    geo = _geocode_pincode(pincode)
    if geo is None:
        return (
            f"Could not find location for pincode {pincode}.\n"
            "Please verify the pincode and try again.\n"
            "Example valid pincodes: 600001 (Chennai Park Town), "
            "600040 (Anna Nagar), 600042 (Velachery)."
        )

    lat, lon, place_name = geo
    short_place = place_name.split(",")[0] if place_name else pincode

    facilities = _overpass_hospitals(lat, lon, radius_m=6000)

    # Widen search if nothing found in 6 km
    if not facilities:
        facilities = _overpass_hospitals(lat, lon, radius_m=15000)

    header = (
        f"Vaccination & Healthcare Centres near Pincode {pincode} "
        f"({short_place})\n"
        f"Coordinates: {lat:.4f}N, {lon:.4f}E  |  Search radius: 6 km\n"
        f"Date requested: {date}\n"
    )
    return _format(facilities, header=header)


def Dose_Availability_District(district_id, date):
    """
    Pipeline:
      1. Map district_id → district name (Tamil Nadu map)
      2. Nominatim  →  district name → (lat, lon)
      3. Overpass   →  (lat, lon) → real hospitals within 10 km
    """
    district_id  = str(district_id).strip()
    district_name = TN_DISTRICT_MAP.get(district_id, "")

    if not district_name:
        return (
            f"Unknown district ID '{district_id}'.\n"
            "Tamil Nadu district IDs: 573 (Chennai), 574 (Kanchipuram), "
            "575 (Tiruvallur), 585 (Coimbatore), 588 (Madurai).\n"
            "Please enter a valid Tamil Nadu district ID."
        )

    geo = _geocode_place(f"{district_name}, Tamil Nadu")
    if geo is None:
        return f"Could not geocode district '{district_name}'. Please try again."

    lat, lon, _ = geo
    facilities   = _overpass_hospitals(lat, lon, radius_m=10000)

    if not facilities:
        facilities = _overpass_hospitals(lat, lon, radius_m=20000)

    header = (
        f"Healthcare Centres in {district_name} District (ID: {district_id})\n"
        f"Coordinates: {lat:.4f}N, {lon:.4f}E  |  Search radius: 10 km\n"
        f"Date requested: {date}\n"
    )
    return _format(facilities, header=header)


def Dose_Availability_Lon_Lat(lattitude, longitude):
    """
    Pipeline:
      Overpass directly with user-supplied coordinates (no geocoding needed).
    """
    try:
        lat = float(str(lattitude).strip())
        lon = float(str(longitude).strip())
    except (TypeError, ValueError):
        return "Invalid coordinates. Please enter valid numbers for latitude and longitude."

    facilities = _overpass_hospitals(lat, lon, radius_m=5000)

    if not facilities:
        facilities = _overpass_hospitals(lat, lon, radius_m=12000)

    header = (
        f"Nearest Healthcare Centres to your GPS location\n"
        f"Your coordinates: Lat {lat:.5f}, Lon {lon:.5f}\n"
        f"Results sorted by proximity (km)\n"
    )
    return _format(facilities, header=header)


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL (unchanged)
# ══════════════════════════════════════════════════════════════════════════════
def send_email(email, message):
    import urllib.request
    import json
    import os

    # Read credentials from environment or creds.txt
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