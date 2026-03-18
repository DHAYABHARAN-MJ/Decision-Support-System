# dss/engine.py
# Hill Construction DSS — Core Scoring Engine
# Source: IS Codes (BIS), NBC 2016, NDMA/GSI Guidelines
# All thresholds are reference values for preliminary screening only.


class DSSEngine:
    """
    Weighted penalty/bonus scoring engine.
    Start score = 100. Apply individual + compound adjustments. Clamp 0–100.
    """

    # ── 1. SLOPE ANGLE (IS 14458, IS 14680, NBC 2016) ───────
    @staticmethod
    def score_slope(slope: float) -> dict:
        if slope <= 15:
            return dict(score=0,   label="Suitable",                  status="ok",
                        action="No action needed.",
                        source="NBC 2016, IS 14458")
        elif slope <= 30:
            return dict(score=-8,  label="Caution",                   status="warn",
                        action="Slope stability analysis required.",
                        source="IS 14680")
        elif slope <= 45:
            return dict(score=-20, label="Steep — earthworks needed", status="warn",
                        action="Retaining wall + cut/fill compulsory.",
                        source="IS 14458")
        else:
            return dict(score=-30, label="Not suitable",              status="danger",
                        action="Construction not recommended.",
                        source="NBC hillside guidelines")

    # ── 2. ELEVATION (IS 875 Part 3, NBC 2016 Part 6) ───────
    @staticmethod
    def score_elevation(elevation: str) -> dict:
        e = elevation.lower()
        if e == "low":
            return dict(score=0,   label="Suitable",            status="ok",
                        action="Standard design applies.",
                        source="NBC 2016 Part 6")
        elif e == "medium":
            return dict(score=-5,  label="Minor constraints",   status="warn",
                        action="Wind load check required.",
                        source="IS 875 Part 3")
        elif e == "high":
            return dict(score=-10, label="Risk — extra design", status="warn",
                        action="Enhanced wind load + access constraints.",
                        source="IS 875 Part 3")
        raise ValueError(f"elevation must be low/medium/high, got: {elevation}")

    # ── 3. LANDSLIDE RISK (NDMA, IS 14458, GSI) ─────────────
    @staticmethod
    def score_landslide(landslide: str) -> dict:
        l = landslide.lower()
        if l == "low":
            return dict(score=0,   label="Suitable",     status="ok",
                        action="Standard construction allowed.",
                        source="NDMA Hazard Zonation")
        elif l == "medium":
            return dict(score=-10, label="Caution",      status="warn",
                        action="Retaining wall + drainage mandatory.",
                        source="IS 14458, NDMA")
        elif l == "high":
            return dict(score=-25, label="Not suitable", status="danger",
                        action="Geotechnical survey + anchoring needed.",
                        source="NDMA, GSI Landslide Atlas")
        raise ValueError(f"landslide_risk must be low/medium/high, got: {landslide}")

    # ── 4. SOIL TYPE (IS 1498, IS 6403, IS 1893) ────────────
    @staticmethod
    def score_soil_type(soil_type: str) -> dict:
        s = soil_type.lower()
        if s == "rock":
            return dict(score=+5,  label="Excellent — stable base",  status="ok",
                        action="Best foundation base.",
                        source="IS 1498, IS 6403")
        elif s == "clay":
            return dict(score=-5,  label="Moderate — swell/shrink",  status="warn",
                        action="Moisture monitoring needed.",
                        source="IS 1498")
        elif s == "sandy":
            return dict(score=-10, label="Weak — liquefaction risk", status="danger",
                        action="Pile/raft compulsory; compaction needed.",
                        source="IS 1498, IS 1893")
        raise ValueError(f"soil_type must be rock/clay/sandy, got: {soil_type}")

    # ── 5. BEARING CAPACITY (IS 6403, IS 1888) ──────────────
    @staticmethod
    def score_bearing_capacity(bearing: float) -> dict:
        if bearing < 50:
            return dict(score=-25, label="Not suitable", status="danger",
                        action="Soil improvement or piling mandatory.",
                        source="IS 6403, IS 1888")
        elif bearing < 100:
            return dict(score=-12, label="Weak soil",    status="warn",
                        action="Raft or pile foundation required.",
                        source="IS 6403")
        elif bearing < 200:
            return dict(score=0,   label="Acceptable",   status="ok",
                        action="Standard foundation design.",
                        source="IS 6403")
        elif bearing < 300:
            return dict(score=+3,  label="Good",         status="ok",
                        action="Broad foundation options available.",
                        source="IS 6403")
        else:
            return dict(score=+5,  label="Excellent",    status="ok",
                        action="All foundation types suitable.",
                        source="IS 6403, IS 1888")

    # ── 6. MOISTURE CONTENT (IS 8009, IS 1904) ──────────────
    @staticmethod
    def score_moisture(moisture: str) -> dict:
        m = moisture.lower()
        if m == "low":
            return dict(score=0,   label="Suitable",              status="ok",
                        action="No additional measure needed.",
                        source="IS 8009")
        elif m == "medium":
            return dict(score=-5,  label="Minor settlement risk", status="warn",
                        action="Monitor and ensure drainage.",
                        source="IS 8009")
        elif m == "high":
            return dict(score=-15, label="High instability risk", status="danger",
                        action="Drainage + soil stabilisation essential.",
                        source="IS 8009, IS 1904")
        raise ValueError(f"moisture_content must be low/medium/high, got: {moisture}")

    # ── 7. NUMBER OF FLOORS (NBC 2016, IS 2911, IS 1893) ────
    @staticmethod
    def score_floors(floors: int) -> dict:
        if floors <= 2:
            return dict(score=0,   label="Suitable",                   status="ok",
                        action="Light load — standard design.",
                        source="NBC 2016 Part 6")
        elif floors <= 5:
            return dict(score=-5,  label="Moderate load",              status="warn",
                        action="Structural engineer review needed.",
                        source="NBC 2016 Part 6")
        elif floors <= 10:
            return dict(score=-12, label="High load — deep foundation", status="warn",
                        action="Pile foundation mandatory.",
                        source="IS 2911, NBC 2016")
        else:
            return dict(score=-20, label="Specialist design required",  status="danger",
                        action="Full geotechnical + structural report needed.",
                        source="IS 2911, IS 1893")

    # ── 8. FOUNDATION TYPE (IS 2911, IS 2950, IS 1904) ──────
    @staticmethod
    def score_foundation(foundation: str) -> dict:
        f = foundation.lower()
        if f == "pile":
            return dict(score=+8,  label="Best for slopes/weak soil",  status="ok",
                        action="Deepest — most stable option.",
                        source="IS 2911")
        elif f == "raft":
            return dict(score=+5,  label="Good load distribution",     status="ok",
                        action="Spreads load — good for weak soil.",
                        source="IS 2950")
        elif f == "stepped":
            return dict(score=+5,  label="Suitable for hilly terrain", status="ok",
                        action="Adapts to slope — hill-specific design.",
                        source="NBC hillside guidelines")
        elif f == "shallow":
            return dict(score=-10, label="Only for flat, strong soil", status="danger",
                        action="Inadequate for slopes or weak soil.",
                        source="IS 1904")
        raise ValueError(f"foundation_type must be pile/raft/stepped/shallow, got: {foundation}")

    # ── 9. BUILDING LOAD (NBC 2016, IS 1904) ────────────────
    @staticmethod
    def score_building_load(load: str) -> dict:
        l = load.lower()
        if l == "light":
            return dict(score=+3,  label="Low soil stress",  status="ok",
                        action="Residential/single floor — low risk.",
                        source="NBC 2016 Part 6")
        elif l == "medium":
            return dict(score=0,   label="Standard load",   status="ok",
                        action="Normal construction — standard design.",
                        source="NBC 2016 Part 6")
        elif l == "heavy":
            return dict(score=-10, label="High stress",     status="danger",
                        action="Strong foundation + soil check mandatory.",
                        source="NBC 2016, IS 1904")
        raise ValueError(f"building_load must be light/medium/heavy, got: {load}")

    # ── 10. CONSTRUCTION MATERIAL (IS 456, IS 800, IS 883) ──
    @staticmethod
    def score_material(material: str) -> dict:
        m = material.lower()
        if m == "concrete":
            return dict(score=+5, label="Strong, durable, seismic-resistant", status="ok",
                        action="Best all-round choice.",
                        source="IS 456, NBC 2016")
        elif m == "steel":
            return dict(score=+5, label="Flexible, good for seismic zones",   status="ok",
                        action="Ideal for high seismic zones.",
                        source="IS 800")
        elif m == "wood":
            return dict(score=-5, label="Weak in moisture + seismic zones",   status="warn",
                        action="Avoid in seismic zone 3+ or wet sites.",
                        source="IS 883, NBC 2016")
        raise ValueError(f"material must be concrete/steel/wood, got: {material}")

    # ── 11. WALL TYPE (IS 456, IS 13920, IS 1905) ───────────
    @staticmethod
    def score_wall_type(wall_type: str) -> dict:
        w = wall_type.lower()
        if w == "reinforced":
            return dict(score=+5, label="Best — lateral + seismic resist.", status="ok",
                        action="Mandatory in seismic zone 3+.",
                        source="IS 456, IS 13920")
        elif w == "brick":
            return dict(score=0,  label="Moderate — brittle under seismic", status="ok",
                        action="Acceptable in low seismic zones.",
                        source="IS 1905")
        elif w == "lightweight":
            return dict(score=-5, label="Weak — not for heavy loads",       status="warn",
                        action="Avoid for multi-floor or heavy use.",
                        source="NBC 2016 Part 6")
        raise ValueError(f"wall_type must be reinforced/brick/lightweight, got: {wall_type}")

    # ── 12. RETAINING WALL (IS 14458) ───────────────────────
    @staticmethod
    def score_retaining_wall(retaining: str, slope: float) -> dict:
        r = retaining.lower()
        if r == "yes":
            return dict(score=+5,  label="Slope stabilised",        status="ok",
                        action="Reduces slope failure risk.",
                        source="IS 14458")
        elif r == "no" and slope <= 15:
            return dict(score=0,   label="No issue (flat land)",    status="ok",
                        action="Flat land — wall not required.",
                        source="IS 14458")
        elif r == "no" and slope > 15:
            return dict(score=-12, label="Risk — no retaining wall", status="danger",
                        action="Install retaining wall before construction.",
                        source="IS 14458, NBC hillside")
        raise ValueError(f"retaining_wall must be yes/no, got: {retaining}")

    # ── 13. DRAINAGE (IS 4111, IS 1904, IS 8009) ────────────
    @staticmethod
    def score_drainage(drainage: str) -> dict:
        d = drainage.lower()
        if d == "yes":
            return dict(score=+3,  label="Controls waterlogging",     status="ok",
                        action="Essential on slopes and clay soils.",
                        source="IS 4111, NBC 2016")
        elif d == "no":
            return dict(score=-10, label="Settlement + erosion risk", status="danger",
                        action="Install sub-surface + perimeter drain.",
                        source="IS 1904, IS 8009")
        raise ValueError(f"drainage must be yes/no, got: {drainage}")

    # ── 14. SEISMIC ZONE (IS 1893 Part 1) ───────────────────
    @staticmethod
    def score_seismic_zone(zone: int) -> dict:
        if zone in [1, 2]:
            return dict(score=0,   label=f"Zone {zone} — Low risk",    status="ok",
                        action="Standard design applies.",
                        source="IS 1893 Part 1")
        elif zone == 3:
            return dict(score=-6,  label="Zone 3 — Moderate risk",     status="warn",
                        action="Shear walls / base isolation needed.",
                        source="IS 1893 Part 1")
        elif zone == 4:
            return dict(score=-12, label="Zone 4 — High risk",         status="danger",
                        action="IS 1893 ductile detailing mandatory.",
                        source="IS 1893 Part 1")
        elif zone == 5:
            return dict(score=-12, label="Zone 5 — Very high risk",    status="danger",
                        action="Full earthquake-resistant design mandatory.",
                        source="IS 1893 Part 1")
        raise ValueError(f"seismic_zone must be 1–5, got: {zone}")

    # ── 15. BUILDING USAGE (NBC 2016 Part 4, IS 1893) ───────
    @staticmethod
    def score_usage(usage: str, landslide: str, seismic_zone: int) -> dict:
        u = usage.lower()
        if u == "residential":
            return dict(score=0,  label="Standard occupancy",               status="ok",
                        action="Normal safety norms apply.",
                        source="NBC 2016 Part 4")
        elif u == "commercial":
            in_hazard = (landslide.lower() == "high" or seismic_zone >= 4)
            return dict(
                score=-5 if in_hazard else 0,
                label="Higher occupancy — stricter norms",
                status="warn" if in_hazard else "ok",
                action="Extra safety checks required in hazard zones." if in_hazard
                       else "Standard commercial norms apply.",
                source="NBC 2016 Part 4, IS 1893"
            )
        raise ValueError(f"usage must be residential/commercial, got: {usage}")

    # ── COMPOUND RULES ───────────────────────────────────────
    @staticmethod
    def apply_compound_rules(p: dict) -> list:
        slope      = p["slope_angle"]
        landslide  = p["landslide_risk"].lower()
        soil_type  = p["soil_type"].lower()
        moisture   = p["moisture_content"].lower()
        floors     = p["num_floors"]
        foundation = p["foundation_type"].lower()
        load       = p["building_load"].lower()
        material   = p["material"].lower()
        wall_type  = p["wall_type"].lower()
        retaining  = p["retaining_wall"].lower()
        drainage   = p["drainage"].lower()
        seismic    = p["seismic_zone"]
        elevation  = p["elevation"].lower()
        triggered  = []

        def add(rule, score, reason, source, rtype):
            triggered.append(dict(rule=rule, score=score, reason=reason,
                                  source=source, type=rtype))

        # DANGER combos
        if load == "heavy" and soil_type == "sandy":
            add("Heavy load + Sandy soil", -15,
                "Liquefaction under load — pile + stabilisation needed.",
                "IS 1893, IS 2911", "danger")

        if floors > 5 and foundation == "shallow":
            add("Floors > 5 + Shallow foundation", -20,
                "Foundation depth inadequate for building height.",
                "IS 2911", "danger")

        if moisture == "high" and drainage == "no":
            add("High moisture + No drainage", -10,
                "Compounding settlement + erosion risk.",
                "IS 8009, IS 1904", "danger")

        if seismic >= 3 and material == "wood":
            add("Seismic zone 3+ + Wood material", -10,
                "Wood fails under lateral seismic forces.",
                "IS 883, IS 1893", "danger")

        if landslide == "high" and retaining == "no":
            add("High landslide + No retaining wall", -12,
                "Slope failure probability very high.",
                "IS 14458", "danger")

        if soil_type == "sandy" and moisture == "high":
            add("Sandy soil + High moisture", -8,
                "Combined liquefaction + settlement risk.",
                "IS 1498, IS 8009", "danger")

        if elevation == "high" and load == "heavy":
            add("High altitude + Heavy building load", -8,
                "Structural stress at altitude + wind load amplified.",
                "IS 875 Part 3", "warn")

        if seismic >= 4 and wall_type == "brick":
            add("Seismic zone 4/5 + Brick walls", -8,
                "Brittle masonry fails under high seismic forces.",
                "IS 1905, IS 1893", "danger")

        if slope > 30 and retaining == "no":
            add("Slope > 30° + No retaining wall", -12,
                "Slope instability without lateral support.",
                "IS 14458", "danger")

        if floors > 10 and seismic >= 4:
            add("Floors > 10 + Seismic zone 4/5", -15,
                "Tall buildings in high seismic zones need specialist review.",
                "IS 1893, IS 2911", "danger")

        # BONUS combos
        if foundation == "pile" and soil_type == "rock":
            add("Pile foundation + Rock soil", +5,
                "Best combination — maximum stability bonus.",
                "IS 2911, IS 6403", "ok")

        if material == "concrete" and wall_type == "reinforced":
            add("Concrete material + Reinforced walls", +5,
                "Best structural material combination.",
                "IS 456, IS 13920", "ok")

        if drainage == "yes" and moisture == "high":
            add("Drainage present + High moisture soil", +5,
                "Drainage mitigates moisture risk effectively.",
                "IS 4111, IS 8009", "ok")

        if seismic <= 2 and load == "light":
            add("Low seismic zone + Light load", +3,
                "Safest combination for hillside construction.",
                "IS 1893, NBC 2016", "ok")

        return triggered

    # ── VERDICT ─────────────────────────────────────────────
    @staticmethod
    def get_verdict(score: int) -> dict:
        if score >= 75:
            return dict(verdict="Feasible", color="green",
                        action="Proceed with standard IS code design.",
                        description="Site conditions are suitable for construction.")
        elif score >= 50:
            return dict(verdict="Feasible with conditions", color="amber",
                        action="Address flagged parameters. Get structural engineer sign-off.",
                        description="Construction possible but certain risks must be mitigated first.")
        elif score >= 30:
            return dict(verdict="High risk — expert review needed", color="orange",
                        action="Mandatory geotechnical + structural expert review required.",
                        description="Multiple high-risk parameters detected. Do not proceed without expert clearance.")
        else:
            return dict(verdict="Not recommended", color="red",
                        action="Do NOT construct. Site conditions unsafe.",
                        description="Site conditions are fundamentally unsafe. Major site remediation required.")

    # ── MAIN ASSESS ─────────────────────────────────────────
    @classmethod
    def assess(cls, p: dict) -> dict:
        individual = {
            "slope_angle":      cls.score_slope(p["slope_angle"]),
            "elevation":        cls.score_elevation(p["elevation"]),
            "landslide_risk":   cls.score_landslide(p["landslide_risk"]),
            "soil_type":        cls.score_soil_type(p["soil_type"]),
            "bearing_capacity": cls.score_bearing_capacity(p["bearing_capacity"]),
            "moisture_content": cls.score_moisture(p["moisture_content"]),
            "num_floors":       cls.score_floors(p["num_floors"]),
            "foundation_type":  cls.score_foundation(p["foundation_type"]),
            "building_load":    cls.score_building_load(p["building_load"]),
            "material":         cls.score_material(p["material"]),
            "wall_type":        cls.score_wall_type(p["wall_type"]),
            "retaining_wall":   cls.score_retaining_wall(p["retaining_wall"], p["slope_angle"]),
            "drainage":         cls.score_drainage(p["drainage"]),
            "seismic_zone":     cls.score_seismic_zone(p["seismic_zone"]),
            "usage":            cls.score_usage(p["usage"], p["landslide_risk"], p["seismic_zone"]),
        }
        compound      = cls.apply_compound_rules(p)
        ind_total     = sum(v["score"] for v in individual.values())
        comp_total    = sum(r["score"] for r in compound)
        final_score   = max(0, min(100, 100 + ind_total + comp_total))
        verdict       = cls.get_verdict(final_score)
        flags         = {k: v for k, v in individual.items() if v["status"] in ("warn", "danger")}
        comp_flags    = [r for r in compound if r["type"] in ("warn", "danger")]
        recommendations = [
            f"{k.replace('_',' ').title()}: {v['action']}"
            for k, v in flags.items()
        ] + [r["reason"] for r in comp_flags]

        return {
            "score": final_score,
            "score_breakdown": {
                "base": 100,
                "individual_total": ind_total,
                "compound_total": comp_total,
            },
            "verdict": verdict,
            "individual_results": individual,
            "compound_rules_triggered": compound,
            "flags": flags,
            "compound_flags": comp_flags,
            "recommendations": recommendations,
            "disclaimer": (
                "This DSS provides preliminary screening only. All thresholds are based on "
                "IS Codes (BIS), NBC 2016, and NDMA/GSI guidelines. Final construction "
                "decisions must be validated by a licensed structural and geotechnical "
                "engineer with site-specific SIR, SPT, and IS 1893 seismic zone verification."
            ),
        }
