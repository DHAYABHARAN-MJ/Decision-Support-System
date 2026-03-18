# Hill Construction DSS

**Decision Support System for Hill Site Construction Feasibility**

Evaluates 15 site parameters against IS Codes (BIS), NBC 2016, and NDMA guidelines
to determine whether construction is feasible on a hillside site.

---

## Quick Start

```bash
# 1. Install dependencies
pip install django djangorestframework

# 2. Run the development server
python manage.py runserver

# 3. Open in browser
http://127.0.0.1:8000/
```

---

## Project Structure

```
hill_construction_dss/
├── manage.py
├── requirements.txt
├── README.md
│
├── hill_dss/                   # Django project config
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py                 # Root URL config
│   └── wsgi.py
│
└── dss/                        # DSS application
    ├── __init__.py
    ├── apps.py
    ├── engine.py               # Core scoring logic (all 15 params + 14 compound rules)
    ├── validators.py           # Input validation
    ├── views.py                # API views (5 endpoints)
    ├── urls.py                 # API URL routes
    ├── tests.py                # 14 automated tests
    └── templates/
        └── dss/
            └── index.html      # Full UI (standalone, works offline too)
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET`  | `/` | Full UI |
| `POST` | `/api/dss/assess/` | Full 15-parameter assessment |
| `POST` | `/api/dss/score/` | Score + verdict only (lightweight) |
| `POST` | `/api/dss/flags/` | Flagged parameters only |
| `GET`  | `/api/dss/rules/` | All 15 parameter rule tables |
| `GET`  | `/api/dss/compound-rules/` | All 14 compound interaction rules |

---

## Sample API Request

```bash
curl -X POST http://127.0.0.1:8000/api/dss/assess/ \
  -H "Content-Type: application/json" \
  -d '{
    "slope_angle": 25,
    "elevation": "medium",
    "landslide_risk": "low",
    "soil_type": "clay",
    "bearing_capacity": 150,
    "moisture_content": "medium",
    "num_floors": 3,
    "foundation_type": "raft",
    "building_load": "medium",
    "material": "concrete",
    "wall_type": "reinforced",
    "retaining_wall": "yes",
    "drainage": "yes",
    "seismic_zone": 3,
    "usage": "residential"
  }'
```

### Sample Response

```json
{
  "score": 82,
  "score_breakdown": {
    "base": 100,
    "individual_total": -23,
    "compound_total": 5
  },
  "verdict": {
    "verdict": "Feasible",
    "color": "green",
    "action": "Proceed with standard IS code design.",
    "description": "Site conditions are suitable for construction."
  },
  "individual_results": { ... },
  "compound_rules_triggered": [ ... ],
  "flags": { ... },
  "recommendations": [ ... ],
  "disclaimer": "..."
}
```

---

## Input Parameters

| Parameter | Type | Values / Range | Source |
|-----------|------|----------------|--------|
| `slope_angle` | float | 0–90° | NBC 2016, IS 14458 |
| `elevation` | string | low / medium / high | IS 875 Part 3 |
| `landslide_risk` | string | low / medium / high | NDMA, IS 14458 |
| `soil_type` | string | rock / clay / sandy | IS 1498, IS 6403 |
| `bearing_capacity` | float | 0–2000 kN/m² | IS 6403, IS 1888 |
| `moisture_content` | string | low / medium / high | IS 8009 |
| `num_floors` | int | 1–50 | NBC 2016, IS 2911 |
| `foundation_type` | string | pile / raft / stepped / shallow | IS 2911, IS 2950 |
| `building_load` | string | light / medium / heavy | NBC 2016 |
| `material` | string | concrete / steel / wood | IS 456, IS 800 |
| `wall_type` | string | reinforced / brick / lightweight | IS 456, IS 13920 |
| `retaining_wall` | string | yes / no | IS 14458 |
| `drainage` | string | yes / no | IS 4111, IS 1904 |
| `seismic_zone` | int | 1–5 | IS 1893 Part 1 |
| `usage` | string | residential / commercial | NBC 2016 Part 4 |

---

## Score Verdicts

| Score | Verdict |
|-------|---------|
| 75–100 | Feasible |
| 50–74 | Feasible with conditions |
| 30–49 | High risk — expert review needed |
| 0–29 | Not recommended |

---

## Running Tests

```bash
python manage.py test dss
```

14 tests covering engine logic, validation, and all API endpoints.

---

## Disclaimer

This DSS provides **preliminary screening only**. All thresholds are based on IS Codes (BIS),
NBC 2016, and NDMA/GSI guidelines. Final construction decisions must be validated by a licensed
structural and geotechnical engineer with site-specific SIR, SPT, and IS 1893 seismic zone verification.
