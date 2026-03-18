# dss/views.py
import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .engine import DSSEngine
from .validators import validate_params, FIELD_RULES


# ── HELPERS ──────────────────────────────────────────────────

def parse_body(request):
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({"error": "Invalid JSON body."}, status=400)


def options_response():
    r = JsonResponse({})
    r["Access-Control-Allow-Origin"]  = "*"
    r["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    r["Access-Control-Allow-Headers"] = "Content-Type"
    return r


def add_cors(response):
    response["Access-Control-Allow-Origin"] = "*"
    return response


# ── 1. FULL ASSESSMENT ───────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class AssessView(View):
    """
    POST /api/dss/assess/
    Full 15-parameter construction feasibility assessment.

    Request JSON:
    {
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
    }

    Response JSON:
    {
        "score": 82,
        "score_breakdown": { "base": 100, "individual_total": -18, "compound_total": 5 },
        "verdict": { "verdict": "Feasible", "color": "green", "action": "...", "description": "..." },
        "individual_results": { ... },
        "compound_rules_triggered": [ ... ],
        "flags": { ... },
        "compound_flags": [ ... ],
        "recommendations": [ ... ],
        "disclaimer": "..."
    }
    """

    def get(self, request):
        return add_cors(JsonResponse({
            "endpoint":    "POST /api/dss/assess/",
            "description": "Full 15-parameter construction feasibility assessment.",
            "required_fields": {
                field: {
                    "type": rules[0].__name__,
                    "allowed" if rules[0] == str else "range": rules[1]
                }
                for field, rules in FIELD_RULES.items()
            },
        }))

    def post(self, request):
        body, err = parse_body(request)
        if err:
            return err
        cleaned, errors = validate_params(body)
        if errors:
            return add_cors(JsonResponse({"errors": errors}, status=422))
        result = DSSEngine.assess(cleaned)
        return add_cors(JsonResponse(result, status=200))

    def options(self, request):
        return options_response()


# ── 2. SCORE ONLY ────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class ScoreOnlyView(View):
    """
    POST /api/dss/score/
    Returns only the final score and verdict — lightweight response.
    """

    def post(self, request):
        body, err = parse_body(request)
        if err:
            return err
        cleaned, errors = validate_params(body)
        if errors:
            return add_cors(JsonResponse({"errors": errors}, status=422))
        result = DSSEngine.assess(cleaned)
        return add_cors(JsonResponse({
            "score":   result["score"],
            "verdict": result["verdict"]["verdict"],
            "color":   result["verdict"]["color"],
            "action":  result["verdict"]["action"],
        }))

    def options(self, request):
        return options_response()


# ── 3. FLAGS ONLY ────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class FlagsOnlyView(View):
    """
    POST /api/dss/flags/
    Returns only warn/danger flagged parameters and compound issues.
    """

    def post(self, request):
        body, err = parse_body(request)
        if err:
            return err
        cleaned, errors = validate_params(body)
        if errors:
            return add_cors(JsonResponse({"errors": errors}, status=422))
        result = DSSEngine.assess(cleaned)
        penalty_from_flags = sum(
            v["score"] for v in result["flags"].values() if v["score"] < 0
        ) + sum(
            r["score"] for r in result["compound_flags"] if r["score"] < 0
        )
        return add_cors(JsonResponse({
            "score":                  result["score"],
            "verdict":                result["verdict"]["verdict"],
            "individual_flags":       result["flags"],
            "compound_flags":         result["compound_flags"],
            "total_penalty_from_flags": penalty_from_flags,
            "recommendations":        result["recommendations"],
        }))

    def options(self, request):
        return options_response()


# ── 4. PARAMETER RULES (read-only reference) ─────────────────

class ParameterRulesView(View):
    """
    GET /api/dss/rules/
    Returns the full rule table for all 15 parameters.
    """

    def get(self, request):
        return add_cors(JsonResponse({
            "total_parameters": 15,
            "scoring_method": "Weighted penalty/bonus from base score of 100. Clamped 0–100.",
            "verdict_ranges": {
                "75–100": "Feasible",
                "50–74":  "Feasible with conditions",
                "30–49":  "High risk — expert review needed",
                "0–29":   "Not recommended",
            },
            "parameter_rules": {
                "slope_angle":      {"type": "numeric", "unit": "degrees", "range": "0–90",     "source": "NBC 2016, IS 14458, IS 14680", "thresholds": [{"range": "0–15","label": "Suitable","score": 0},{"range": "16–30","label": "Caution","score": -8},{"range": "31–45","label": "Steep","score": -20},{"range": "46–90","label": "Not suitable","score": -30}]},
                "elevation":        {"type": "categorical", "allowed": ["low","medium","high"], "source": "IS 875 Part 3, NBC 2016 Part 6", "thresholds": [{"value": "low","label": "Suitable","score": 0},{"value": "medium","label": "Minor constraints","score": -5},{"value": "high","label": "Risk","score": -10}]},
                "landslide_risk":   {"type": "categorical", "allowed": ["low","medium","high"], "source": "NDMA, IS 14458, GSI", "thresholds": [{"value": "low","label": "Suitable","score": 0},{"value": "medium","label": "Caution","score": -10},{"value": "high","label": "Not suitable","score": -25}]},
                "soil_type":        {"type": "categorical", "allowed": ["rock","clay","sandy"], "source": "IS 1498, IS 6403, IS 1893", "thresholds": [{"value": "rock","label": "Excellent","score": 5},{"value": "clay","label": "Moderate","score": -5},{"value": "sandy","label": "Weak","score": -10}]},
                "bearing_capacity": {"type": "numeric", "unit": "kN/m²", "range": "0–2000",    "source": "IS 6403, IS 1888", "thresholds": [{"range": "<50","label": "Not suitable","score": -25},{"range": "50–99","label": "Weak","score": -12},{"range": "100–199","label": "Acceptable","score": 0},{"range": "200–299","label": "Good","score": 3},{"range": "300+","label": "Excellent","score": 5}]},
                "moisture_content": {"type": "categorical", "allowed": ["low","medium","high"], "source": "IS 8009, IS 1904", "thresholds": [{"value": "low","label": "Suitable","score": 0},{"value": "medium","label": "Minor risk","score": -5},{"value": "high","label": "High risk","score": -15}]},
                "num_floors":       {"type": "numeric", "unit": "count", "range": "1–50",       "source": "NBC 2016, IS 2911, IS 1893", "thresholds": [{"range": "1–2","label": "Suitable","score": 0},{"range": "3–5","label": "Moderate","score": -5},{"range": "6–10","label": "High","score": -12},{"range": "11+","label": "Specialist","score": -20}]},
                "foundation_type":  {"type": "categorical", "allowed": ["pile","raft","stepped","shallow"], "source": "IS 2911, IS 2950, IS 1904", "thresholds": [{"value": "pile","label": "Best","score": 8},{"value": "raft","label": "Good","score": 5},{"value": "stepped","label": "Good","score": 5},{"value": "shallow","label": "Risk","score": -10}]},
                "building_load":    {"type": "categorical", "allowed": ["light","medium","heavy"], "source": "NBC 2016, IS 1904", "thresholds": [{"value": "light","label": "Low stress","score": 3},{"value": "medium","label": "Standard","score": 0},{"value": "heavy","label": "High stress","score": -10}]},
                "material":         {"type": "categorical", "allowed": ["concrete","steel","wood"], "source": "IS 456, IS 800, IS 883", "thresholds": [{"value": "concrete","label": "Strong","score": 5},{"value": "steel","label": "Flexible","score": 5},{"value": "wood","label": "Weak","score": -5}]},
                "wall_type":        {"type": "categorical", "allowed": ["reinforced","brick","lightweight"], "source": "IS 456, IS 13920, IS 1905", "thresholds": [{"value": "reinforced","label": "Best","score": 5},{"value": "brick","label": "Moderate","score": 0},{"value": "lightweight","label": "Weak","score": -5}]},
                "retaining_wall":   {"type": "categorical", "allowed": ["yes","no"], "source": "IS 14458", "note": "Score context-dependent on slope angle"},
                "drainage":         {"type": "categorical", "allowed": ["yes","no"], "source": "IS 4111, IS 1904, IS 8009", "thresholds": [{"value": "yes","label": "Controls waterlogging","score": 3},{"value": "no","label": "Settlement risk","score": -10}]},
                "seismic_zone":     {"type": "numeric", "unit": "zone", "range": "1–5",         "source": "IS 1893 Part 1", "thresholds": [{"value": 1,"label": "Very low","score": 0},{"value": 2,"label": "Low","score": 0},{"value": 3,"label": "Moderate","score": -6},{"value": 4,"label": "High","score": -12},{"value": 5,"label": "Very high","score": -12}]},
                "usage":            {"type": "categorical", "allowed": ["residential","commercial"], "source": "NBC 2016 Part 4, IS 1893", "note": "Commercial -5 only in high landslide or seismic zone 4/5"},
            },
        }))


# ── 5. COMPOUND RULES (read-only reference) ──────────────────

class CompoundRulesView(View):
    """
    GET /api/dss/compound-rules/
    Returns all 14 compound interaction rules.
    """

    def get(self, request):
        rules = [
            {"rule": "Heavy load + Sandy soil",          "score": -15, "source": "IS 1893, IS 2911",   "type": "danger"},
            {"rule": "Floors > 5 + Shallow foundation",  "score": -20, "source": "IS 2911",            "type": "danger"},
            {"rule": "High moisture + No drainage",       "score": -10, "source": "IS 8009, IS 1904",   "type": "danger"},
            {"rule": "Seismic zone 3+ + Wood material",  "score": -10, "source": "IS 883, IS 1893",    "type": "danger"},
            {"rule": "High landslide + No retaining wall","score": -12, "source": "IS 14458",           "type": "danger"},
            {"rule": "Sandy soil + High moisture",        "score": -8,  "source": "IS 1498, IS 8009",   "type": "danger"},
            {"rule": "High altitude + Heavy load",        "score": -8,  "source": "IS 875 Part 3",      "type": "warn"},
            {"rule": "Seismic zone 4/5 + Brick walls",   "score": -8,  "source": "IS 1905, IS 1893",   "type": "danger"},
            {"rule": "Slope > 30° + No retaining wall",  "score": -12, "source": "IS 14458",           "type": "danger"},
            {"rule": "Floors > 10 + Seismic zone 4/5",  "score": -15, "source": "IS 1893, IS 2911",   "type": "danger"},
            {"rule": "Pile foundation + Rock soil",       "score": +5,  "source": "IS 2911, IS 6403",   "type": "ok"},
            {"rule": "Concrete + Reinforced walls",       "score": +5,  "source": "IS 456, IS 13920",   "type": "ok"},
            {"rule": "Drainage present + High moisture",  "score": +5,  "source": "IS 4111, IS 8009",   "type": "ok"},
            {"rule": "Low seismic zone + Light load",     "score": +3,  "source": "IS 1893, NBC 2016",  "type": "ok"},
        ]
        return add_cors(JsonResponse({
            "total_compound_rules": len(rules),
            "description": "Applied additionally when two conditions co-exist. Scores stack on top of individual scores.",
            "rules": rules,
        }))
