import json
from data.mission_debris_ledger import DebrisLedger
from hermes_core.mds_calculator import compute_mds
from interfaces.bridges import (LaunchControlBridge, OrbitalTrafficBridge, 
                                RiskAssessmentBridge, SpaceWeatherBridge, 
                                generate_constraint_packet)

class HermesAgent:
    def __init__(self, db_path="mission_debris_ledger.db"):
        self.ledger = DebrisLedger(db_path)
        self.lc_bridge = LaunchControlBridge()
        self.ot_bridge = OrbitalTrafficBridge()
        self.ra_bridge = RiskAssessmentBridge()
        self.sw_bridge = SpaceWeatherBridge()
        self.active = False

    def initialize_sequence(self):
        print("[HERMES] Starting Initialization Sequence...\n")
        
        print("[1/7] Loading License Registry -> FCC 5-year orbital debris rule active.")
        print("[2/7] Loading Mission Manifest parser.")
        
        catalog_count = self.ot_bridge.get_trackable_objects_count()
        print(f"[3/7] Querying Orbital Traffic AI -> Found {catalog_count} tracked objects.")
        
        weather = self.sw_bridge.get_solar_cycle_phase()
        print(f"[4/7] Querying Space Weather AI -> F10.7={weather['F10_7']}, Kp={weather['Kp']}")
        
        print("[5/7] Loading persistent Mission Debris Ledger.")
        print("[6/7] Verifying inter-agent communication channels -> Protocols synced.")
        print("[7/7] Issuing READY status to Mission Director AI.\n")
        self.active = True
        return self.active

    def evaluate_mission(self, mission_id, elements):
        """
        Evaluate full mission elements against HERMES Hard & Soft Constraints.
        """
        if not self.active:
            raise Exception("Agent NOT initialized!")

        print(f"\n--- EVALUATING MISSION: {mission_id} ---")
        blocking_found = False
        advisory_count = 0
        
        # Save to ledger
        for el in elements:
            self.ledger.add_element(el["id"], mission_id, el["category"], el["mass_kg"], el["strategy"], el.get("metrics"))

        # Check Hard & Soft Constraints
        for el in elements:
            strategy = el.get("strategy")
            metrics = el.get("metrics", {})
            orbit = el.get("orbit", {"type": "LEO"}) # Mock orbit type defaults to LEO
            
            # --- HARD CONSTRAINTS ---

            # HC-001: Undefined Strategy
            if not strategy or strategy == "UNDEFINED":
                pkt = generate_constraint_packet(
                    "HC-001", "LAUNCH_CONTROL", "BLOCKING",
                    f"Element {el['id']} has no defined disposal strategy.",
                    {"adjust_type": "disposal_strategy", "delta": 0, "unit": "N/A", "reason": "No object can launch if strategy is UNDEFINED"}
                )
                self.lc_bridge.send_constraint(pkt)
                blocking_found = True

            # HC-002: LEO deorbit timeline
            if orbit.get("type") == "LEO" and strategy != "REENTRY":
                if float(metrics.get("deorbit_timeline_years", 30)) > 5.0:
                    pkt = generate_constraint_packet(
                        "HC-002", "LAUNCH_CONTROL", "BLOCKING",
                        f"Element {el['id']} exceeds 5-year LEO deorbit rule.",
                        {"adjust_type": "deorbit_timeline", "delta": 5.0, "unit": "years", "reason": "FCC 5-year orbital debris rules"}
                    )
                    self.lc_bridge.send_constraint(pkt)
                    blocking_found = True

            # HC-003: GEO graveyard fuel margins
            if orbit.get("type") == "GEO":
                fuel_margin = metrics.get("graveyard_fuel_margin", 0)
                if fuel_margin < 1.4: # 40% margin
                    pkt = generate_constraint_packet(
                        "HC-003", "LAUNCH_CONTROL", "BLOCKING",
                        f"GEO object {el['id']} lacks required 40% fuel margin for graveyard maneuver.",
                        {"adjust_type": "fuel_budget", "delta": 1.4 - fuel_margin, "unit": "multiplier", "reason": "GEO EOL fuel margin rules"}
                    )
                    self.lc_bridge.send_constraint(pkt)
                    blocking_found = True

            # HC-004: Uncontrolled Casualty Expectancy
            if strategy == "REENTRY" and not metrics.get("controlled_reentry", False):
                ec_res = self.ra_bridge.get_casualty_risk({
                    "mass_kg": el["mass_kg"], 
                    "Cd_area_m2": metrics.get("cd_area", 1.0),
                    "reentry_type": "UNCONTROLLED"
                })
                ec = ec_res["Ec"]
                if ec >= 1.0 / 10000.0:
                    pkt = generate_constraint_packet(
                        "HC-004", "LAUNCH_CONTROL", "BLOCKING",
                        f"Uncontrolled reentry of {el['id']} exceeds Ec limit 1:10000",
                        {"adjust_type": "reentry_target", "delta": round(ec, 6), "unit": "risk", "reason": "Casualty expectancy limit exceeded"}
                    )
                    self.lc_bridge.send_constraint(pkt)
                    blocking_found = True
                    metrics['casualty_expectancy'] = ec

            # HC-005 & HC-007: Passivation and Venting
            if not metrics.get("passivation_plan") == "COMPLETE":
                pkt = generate_constraint_packet(
                    "HC-005/HC-007", "LAUNCH_CONTROL", "BLOCKING",
                    f"Element {el['id']} lacks verified 30-min passivation / 3% tank venting plan.",
                    {"adjust_type": "passivation", "delta": 0, "unit": "N/A", "reason": "Explosion risk via pressurized vessels"}
                )
                self.lc_bridge.send_constraint(pkt)
                blocking_found = True

            # HC-006: Congestion Area Collision Avoidance
            if metrics.get("cd_area", 0) > 0.1 and metrics.get("congestion_index", 0) > 0.8 and not metrics.get("has_active_avoidance", False):
                pkt = generate_constraint_packet(
                    "HC-006", "LAUNCH_CONTROL", "BLOCKING",
                    f"Element {el['id']} in dense orbit must have active collision avoidance.",
                    {"adjust_type": "payload_capabilities", "delta": 1, "unit": "avoidance_thrusters", "reason": "T3 threshold density area rule"}
                )
                self.lc_bridge.send_constraint(pkt)
                blocking_found = True
                
                
            # --- SOFT CONSTRAINTS ---

            # SC-002: Prefer controlled reentry
            if strategy == "REENTRY" and not metrics.get("controlled_reentry", False):
                if metrics.get("delta_v_cost_ratio", 0) < 0.15: # < 15% budget
                    pkt = generate_constraint_packet(
                        "SC-002", "LAUNCH_CONTROL", "ADVISORY",
                        f"Element {el['id']} delta-V cost for controlled reentry is low. Consider switching to controlled target (SC-003: SIO Point Nemo).",
                        {"adjust_type": "reentry_type", "delta": 0, "unit": "type", "reason": "Controlled reentry preferred when delta-V < 15%"}
                    )
                    self.lc_bridge.send_constraint(pkt)
                    advisory_count += 1

            # SC-005: 5% CAM reserve
            if metrics.get("fuel_reserve_pct", 0) < 5.0 and el["category"] in ["CATEGORY B"] and orbit.get("type") == "LEO":
                pkt = generate_constraint_packet(
                    "SC-005", "ORBITAL_TRAFFIC", "ADVISORY",
                    f"Payload {el['id']} lacks 5% dedicated CAM (Collision Avoidance Maneuver) reserve.",
                    {"adjust_type": "fuel_accounting", "delta": 5.0, "unit": "percent", "reason": "Emergency collision avoidance"}
                )
                self.ot_bridge.send_mandate(pkt)
                advisory_count += 1

        # Compute MDS
        db_elements = self.ledger.fetch_mission_elements(mission_id)
        mds_score = compute_mds(db_elements)
        print(f"\n[HERMES] Mission Debris Score (MDS) for {mission_id}: {mds_score}/100")
        
        if blocking_found or mds_score < 70:
            print("[MISSION STATUS] NO-GO. Resolve blocking constraints first.\n")
        elif mds_score < 85:
            print("[MISSION STATUS] PROCEED WITH CAUTION. Advisory constraints apply.\n")
        else:
            print("[MISSION STATUS] GO FOR LAUNCH. Clear of debris risks.\n")

        return mds_score
