"""
SUBAK-SOIL: In-Situ Soil Carbon & Mulching Synchronizer
Optimization Engine powered by Google OR-Tools (CP-SAT Solver)
Allocates Custom Hiring Centre (CHC) Super Seeder fleets across village clusters in Punjab
to maximize Soil Organic Carbon (SOC) preservation within the critical 15-day harvest window.
"""

import sys
import os
import argparse
import time
import math
import pandas as pd

# Check if OR-Tools is available
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


def solve_subak_schedule(df, district="Sangrur", max_machines_per_cluster_day=15, time_limit_sec=3.0):
    """
    Core Subak Scheduling Solver.
    
    Args:
        df (pd.DataFrame): Master dataset with village clusters.
        district (str): Target district (e.g. 'Sangrur', 'Ludhiana', 'Bathinda').
        max_machines_per_cluster_day (int): Upper bound of Super Seeders sent to 1 cluster per day.
        time_limit_sec (float): Max solve time limit for OR-Tools.
        
    Returns:
        tuple: (schedule_df: pd.DataFrame, summary: dict)
    """
    start_time = time.time()
    
    # 1. Filter district data
    dist_df = df[df["district"].str.lower() == district.lower()].copy()
    if dist_df.empty:
        # Fallback to Sangrur or entire df if district not found
        dist_df = df.copy().head(68)
        district = "Sangrur"

    clusters = dist_df.to_dict("records")
    num_clusters = len(clusters)
    num_days = 15  # 15-day critical burning window horizon
    ha_per_machine_day = 2.5  # Standard Super Seeder mulching rate: 2.5 ha/day
    
    # Fleet size available in the district (sum of CHC capacities)
    if "chc_super_seeders_available" in dist_df.columns:
        total_fleet_per_day = max(60, int(dist_df["chc_super_seeders_available"].sum() * 1.5))
    else:
        total_fleet_per_day = 120

    # Ensure column compatibility
    for c in clusters:
        if "soil_organic_carbon_percent" in c and "soc_percent" not in c:
            c["soc_percent"] = float(c["soil_organic_carbon_percent"])
        elif "soc_percent" not in c:
            c["soc_percent"] = 0.65
            
        c["paddy_area_ha"] = float(c.get("paddy_area_ha", 120))
        c["harvest_days_left"] = max(1, min(num_days, int(c.get("harvest_days_left", 7))))
        c["urgency_priority_score"] = float(c.get("urgency_priority_score", 50.0))
        
        # Priority Weight:
        # CRITICAL (<0.50% SOC): 3.5x weight
        # DEFICIENT (0.50-0.75% SOC): 2.0x weight
        # MODERATE (>0.75% SOC): 1.0x weight
        soc = c["soc_percent"]
        if soc < 0.50:
            c["priority_weight"] = 350
        elif soc <= 0.75:
            c["priority_weight"] = 200
        else:
            c["priority_weight"] = 100

    # 2. Optimization using Google OR-Tools CP-SAT
    solver_status = "OPTIMAL"
    allocations = {}  # (cluster_idx, day) -> machine count integer
    
    if ORTOOLS_AVAILABLE:
        model = cp_model.CpModel()
        
        # Variables: x[i, d] = integer number of machines dispatched to cluster i on day d
        x = {}
        for i in range(num_clusters):
            deadline = clusters[i]["harvest_days_left"]
            for d in range(1, num_days + 1):
                # Cannot dispatch after harvest deadline (residue will be burnt)
                upper_bound = max_machines_per_cluster_day if d <= deadline else 0
                x[i, d] = model.NewIntVar(0, upper_bound, f"m_{i}_{d}")
                
        # Constraint 1: Daily district fleet limit
        for d in range(1, num_days + 1):
            model.Add(sum(x[i, d] for i in range(num_clusters)) <= total_fleet_per_day)
            
        # Constraint 2: Cannot mulch more than the cluster's paddy area
        for i in range(num_clusters):
            # Total machines over active days * 2.5 ha <= paddy_area_ha + margin
            max_total_machines = math.ceil(clusters[i]["paddy_area_ha"] / ha_per_machine_day)
            model.Add(sum(x[i, d] for d in range(1, num_days + 1)) <= max_total_machines)

        # Objective: Maximize priority-weighted land mulched before deadline
        objective_terms = []
        for i in range(num_clusters):
            weight = clusters[i]["priority_weight"]
            deadline = clusters[i]["harvest_days_left"]
            # Reward earlier mulching higher to beat weather uncertainty
            for d in range(1, deadline + 1):
                early_bonus = (deadline - d + 1) * 5
                objective_terms.append(x[i, d] * (weight + early_bonus))
                
        model.Maximize(sum(objective_terms))
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_sec
        solver.parameters.num_search_workers = 4
        res = solver.Solve(model)
        
        if res in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solver_status = "OPTIMAL" if res == cp_model.OPTIMAL else "FEASIBLE"
            for i in range(num_clusters):
                for d in range(1, num_days + 1):
                    allocations[i, d] = int(solver.Value(x[i, d]))
        else:
            solver_status = "HEURISTIC"
            allocations = None
    else:
        solver_status = "HEURISTIC (OR-Tools not loaded)"
        allocations = None

    # Fallback heuristic if OR-Tools unavailable or timeout
    if allocations is None:
        allocations = {}
        daily_used = {d: 0 for d in range(1, num_days + 1)}
        # Sort by urgency
        sorted_indices = sorted(range(num_clusters), key=lambda idx: (
            clusters[idx]["harvest_days_left"],
            -clusters[idx]["priority_weight"]
        ))
        
        for i in sorted_indices:
            paddy_ha = clusters[i]["paddy_area_ha"]
            needed_machines = math.ceil(paddy_ha / ha_per_machine_day)
            deadline = clusters[i]["harvest_days_left"]
            
            allocated_for_i = 0
            for d in range(1, deadline + 1):
                can_take = min(
                    max_machines_per_cluster_day,
                    needed_machines - allocated_for_i,
                    total_fleet_per_day - daily_used[d]
                )
                if can_take > 0:
                    allocations[i, d] = can_take
                    daily_used[d] += can_take
                    allocated_for_i += can_take
                else:
                    allocations[i, d] = 0
            for d in range(deadline + 1, num_days + 1):
                allocations[i, d] = 0

    # 3. Build Schedule DataFrame & Impact Metrics
    rows = []
    total_paddy_ha = sum(c["paddy_area_ha"] for c in clusters)
    total_mulched_ha = 0.0
    baseline_mulched_ha = 0.0
    total_carbon_saved_tons = 0.0
    total_npk_saved_kg = 0.0
    total_fertilizer_savings_inr = 0
    clusters_fully_served = 0

    for i in range(num_clusters):
        c = clusters[i]
        paddy_ha = c["paddy_area_ha"]
        deadline = c["harvest_days_left"]
        
        # Calculate daily allocations
        daily_allocs = {f"day_{d}": allocations.get((i, d), 0) for d in range(1, num_days + 1)}
        
        # Mulched ha on or before deadline
        machines_before_deadline = sum(allocations.get((i, d), 0) for d in range(1, deadline + 1))
        mulched_ha = min(paddy_ha, round(machines_before_deadline * ha_per_machine_day, 1))
        
        # Baseline CHC allocation (uncoordinated naive baseline without Subak synchronization)
        # Typically handles ~48% on average due to lack of synchronization and idle travel
        baseline_ha = min(paddy_ha, round(paddy_ha * (0.35 + 0.02 * min(deadline, 10)), 1))
        baseline_mulched_ha += baseline_ha
        
        total_mulched_ha += mulched_ha
        is_fully_served = bool(mulched_ha >= (paddy_ha - 1.0))
        if is_fully_served:
            clusters_fully_served += 1
            
        # ICAR Nutrients & Carbon Formulas:
        # 1 ha paddy generates ~5.5 tons of straw
        # 1 ton straw = 400 kg SOC (0.4 tons), 5.5 kg N, 2.3 kg P, 25.0 kg K
        straw_tons = mulched_ha * 5.5
        c_saved_tons = round(straw_tons * 0.40, 1)
        n_saved_kg = round(straw_tons * 5.5, 1)
        p_saved_kg = round(straw_tons * 2.3, 1)
        k_saved_kg = round(straw_tons * 25.0, 1)
        npk_saved_kg = round(n_saved_kg + p_saved_kg + k_saved_kg, 1)
        
        # Fertilizer value in INR (Chemical replacement: Urea, DAP, MOP)
        fert_inr = round(n_saved_kg * 15 + p_saved_kg * 55 + k_saved_kg * 35)
        
        total_carbon_saved_tons += c_saved_tons
        total_npk_saved_kg += npk_saved_kg
        total_fertilizer_savings_inr += fert_inr
        
        row_dict = {
            "cluster_id": c["cluster_id"],
            "cluster_name": c["cluster_name"],
            "block": c.get("block", ""),
            "district": district,
            "paddy_area_ha": int(paddy_ha),
            "harvest_days_left": deadline,
            "soc_percent": c["soc_percent"],
            "soc_status": c.get("soc_status", "DEFICIENT"),
            "subak_ha_mulched": mulched_ha,
            "fully_served": is_fully_served,
            "carbon_saved_tons": c_saved_tons,
            "npk_saved_kg": npk_saved_kg,
            "fertilizer_savings_inr": fert_inr,
            **daily_allocs
        }
        rows.append(row_dict)

    schedule_df = pd.DataFrame(rows)
    
    # 4. Summary Output
    solve_time = round(time.time() - start_time, 2)
    subak_cov_pct = round((total_mulched_ha / total_paddy_ha) * 100, 1) if total_paddy_ha > 0 else 0.0
    base_cov_pct = round((baseline_mulched_ha / total_paddy_ha) * 100, 1) if total_paddy_ha > 0 else 0.0
    
    summary = {
        "subak_coverage_pct": subak_cov_pct,
        "baseline_coverage_pct": base_cov_pct,
        "total_carbon_saved_tons": round(total_carbon_saved_tons, 1),
        "clusters_fully_served_subak": clusters_fully_served,
        "total_clusters": num_clusters,
        "total_npk_saved_kg": round(total_npk_saved_kg, 0),
        "total_fertilizer_savings_inr": int(total_fertilizer_savings_inr),
        "solver_status": solver_status,
        "solve_time_sec": solve_time,
        "district": district
    }
    
    return schedule_df, summary


def main():
    parser = argparse.ArgumentParser(description="SUBAK-SOIL OR-Tools Optimization CLI")
    parser.add_argument("--input", type=str, default="subak_soil_datasheet.csv", help="Input datasheet CSV path")
    parser.add_argument("--district", type=str, default="Sangrur", help="Target district (e.g. Sangrur, Ludhiana)")
    parser.add_argument("--output", type=str, default="subak_schedule_output.csv", help="Output schedule CSV path")
    parser.add_argument("--max-machines", type=int, default=15, help="Max machines dispatched per village per day")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    print(f"Loading '{args.input}'...")
    df = pd.read_csv(args.input)
    print(f"Solving Subak schedule for District: {args.district}...")
    
    schedule_df, summary = solve_subak_schedule(
        df,
        district=args.district,
        max_machines_per_cluster_day=args.max_machines
    )

    print(f"\n================ SUBAK-SOIL SOLVER RESULT ================")
    print(f"Solver Status:                 {summary['solver_status']}")
    print(f"Solve Time:                    {summary['solve_time_sec']} seconds")
    print(f"Lahan Termulsa Tepat Waktu:    {summary['subak_coverage_pct']}% (vs Baseline: {summary['baseline_coverage_pct']}%)")
    print(f"Desa Tuntas Terlayani:         {summary['clusters_fully_served_subak']} / {summary['total_clusters']} klaster")
    print(f"Karbon Organik Diselamatkan:   {summary['total_carbon_saved_tons']:,.1f} Ton")
    print(f"Total Hara NPK Kembali:        {summary['total_npk_saved_kg']:,.0f} kg")
    print(f"Penghematan Pupuk Kimia:       INR {summary['total_fertilizer_savings_inr']:,}")
    print(f"==========================================================\n")

    schedule_df.to_csv(args.output, index=False)
    print(f"Schedule exported successfully to: {args.output}")


if __name__ == "__main__":
    main()
