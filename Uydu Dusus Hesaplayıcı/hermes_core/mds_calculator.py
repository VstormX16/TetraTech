def calculate_casualty_expectancy(mass_kg, cd_area, orbit_data, is_controlled):
    """
    Mock calculation for Casualty Expectancy (Ec)
    Ec = Fc (Fragmentation casualty area) * Ac (Cross-section) * Pd (Population density)
    For uncontrolled reentry, this is usually higher.
    """
    if is_controlled:
        return 1 / 100000.0  # Very safe (e.g., Point Nemo targeted)
    
    # Very basic placeholder logic for UNCONTROLLED
    base_ec = (mass_kg * cd_area) / 1000000.0
    return base_ec

def compute_mds(mission_elements):
    """
    Compute Mission Debris Score (MDS) from 0-100.
    100 = Zero debris risk
    0 = Maximum risk
    
    Components:
    - Disposal strategy completeness: 30 points
    - Ec (casualty risk) margin: 20 points
    - Regulatory compliance: 20 points
    - Orbital regime congestion factor: 15 points
    - Passivation plan quality: 15 points
    """
    if not mission_elements:
        return 0
        
    total_score = 0
    num_elements = len(mission_elements)
    
    for element in mission_elements:
        element_score = 0
        
        # 1. Disposal strategy completeness (30 pts)
        strategy = element.get('disposal_strategy', 'UNDEFINED')
        if strategy in ['REENTRY', 'GRAVEYARD', 'RETRIEVAL']:
            element_score += 30
        
        # 2. Ec margin (20 pts)
        metrics = element.get('metrics', {})
        ec = metrics.get('casualty_expectancy', 1.0)
        if ec < 1/10000.0:
            element_score += 20
        elif ec < 1/8000.0:
            element_score += 10 # Gray zone
            
        # 3. Regulatory compliance (20 pts)
        # Simplified: if proper fuel margins exist and 25-yr rule is met
        compliance_met = metrics.get('regulatory_compliant', False)
        if compliance_met:
            element_score += 20
            
        # 4. Congestion factor (15 pts)
        congestion = metrics.get('congestion_index', 1.0) # 0.0 to 1.0 (1.0 = clear)
        element_score += (15 * congestion)
        
        # 5. Passivation plan quality (15 pts)
        passivation_plan = metrics.get('passivation_plan', 'NONE')
        if passivation_plan == 'COMPLETE':
            element_score += 15
        elif passivation_plan == 'PARTIAL':
            element_score += 7
            
        total_score += element_score
        
    # Average score across all mission separating elements
    avg_mds = total_score / num_elements
    return round(avg_mds, 1)
