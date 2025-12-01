"""
Test Script for AD Compliance Evaluation

Tests 10 aircraft configurations against FAA AD 2025-23-53 and EASA AD 2025-0254
"""

import json
from ad_compliance_schema import AircraftConfiguration
from ad_compliance_engine import ADComplianceEngine, format_results_table


def main():
    """Run compliance checks on test aircraft fleet"""
    
    # Initialize the compliance engine
    print("Loading AD rules...")
    engine = ADComplianceEngine("ad_rules.json")
    print(f"Loaded {len(engine.ads)} ADs")
    for ad in engine.ads:
        print(f"  - {ad.ad_id}: {ad.title}")
    print()
    
    # Define test aircraft fleet
    test_fleet = [
        AircraftConfiguration(
            aircraft_model="MD-11",
            msn=48123,
            modifications=[]
        ),
        AircraftConfiguration(
            aircraft_model="DC-10-30F",
            msn=47890,
            modifications=[]
        ),
        AircraftConfiguration(
            aircraft_model="Boeing 737-800",
            msn=30123,
            modifications=[]
        ),
        AircraftConfiguration(
            aircraft_model="A320-214",
            msn=5234,
            modifications=[]
        ),
        AircraftConfiguration(
            aircraft_model="A320-232",
            msn=6789,
            modifications=["mod 24591 (production)"]
        ),
        AircraftConfiguration(
            aircraft_model="A320-214",
            msn=7456,
            modifications=["SB A320-57-1089 Rev 04"]
        ),
        AircraftConfiguration(
            aircraft_model="A321-111",
            msn=8123,
            modifications=[]
        ),
        AircraftConfiguration(
            aircraft_model="A321-112",
            msn=364,
            modifications=["mod 24977 (production)"]
        ),
        AircraftConfiguration(
            aircraft_model="A319-100",
            msn=9234,
            modifications=[]
        ),
        AircraftConfiguration(
            aircraft_model="MD-10-10F",
            msn=46234,
            modifications=[]
        ),
    ]
    
    print(f"Testing {len(test_fleet)} aircraft configurations...\n")
    print("=" * 100)
    
    # Evaluate entire fleet
    fleet_results = engine.evaluate_fleet(test_fleet)
    
    # Print summary table
    print("\nSUMMARY TABLE")
    print("=" * 100)
    print()
    
    # Create custom table format matching the assignment requirements
    print(f"{'Aircraft Model':<20} {'MSN':<10} {'Modifications':<35} {'FAA-2025-23-53':<20} {'EASA-2025-0254':<20}")
    print("-" * 105)
    
    for aircraft in test_fleet:
        aircraft_id = f"{aircraft.aircraft_model}-{aircraft.msn}"
        results = fleet_results[aircraft_id]
        
        # Get results for each AD
        faa_result = next((r for r in results if r.ad_id == "FAA-2025-23-53"), None)
        easa_result = next((r for r in results if r.ad_id == "EASA-2025-0254"), None)
        
        mods_str = ", ".join(aircraft.modifications) if aircraft.modifications else "None"
        
        print(f"{aircraft.aircraft_model:<20} {aircraft.msn:<10} {mods_str:<35} {faa_result.status:<20} {easa_result.status:<20}")
    
    print()
    print("=" * 100)
    
    # Print detailed results for each aircraft
    print("\n\nDETAILED RESULTS")
    print("=" * 100)
    
    for aircraft in test_fleet:
        aircraft_id = f"{aircraft.aircraft_model}-{aircraft.msn}"
        results = fleet_results[aircraft_id]
        
        print(f"\n{'=' * 100}")
        print(f"Aircraft: {aircraft.aircraft_model} | MSN: {aircraft.msn}")
        print(f"Modifications: {', '.join(aircraft.modifications) if aircraft.modifications else 'None'}")
        print(f"{'=' * 100}")
        
        for result in results:
            print(f"\n  AD: {result.ad_id}")
            print(f"  Status: {result.status.upper()}")
            print(f"  Is Affected: {result.is_affected}")
            print(f"  Reasoning: {result.reason}")
            print(f"  {'-' * 96}")
    
    # Export results to JSON
    print("\n\nExporting results to JSON...")
    
    results_export = []
    for aircraft in test_fleet:
        aircraft_id = f"{aircraft.aircraft_model}-{aircraft.msn}"
        results = fleet_results[aircraft_id]
        
        aircraft_result = {
            "aircraft_model": aircraft.aircraft_model,
            "msn": aircraft.msn,
            "modifications": aircraft.modifications,
            "ad_results": {}
        }
        
        for result in results:
            aircraft_result["ad_results"][result.ad_id] = {
                "status": result.status,
                "is_affected": result.is_affected,
                "reason": result.reason
            }
        
        results_export.append(aircraft_result)
    
    with open("test_results.json", "w") as f:
        json.dump(results_export, f, indent=2)
    
    print("Results exported to test_results.json")
    
    # Print summary statistics
    print("\n\nSUMMARY STATISTICS")
    print("=" * 100)
    
    faa_affected = sum(1 for aircraft in test_fleet 
                       if fleet_results[f"{aircraft.aircraft_model}-{aircraft.msn}"][0].status == "yes")
    easa_affected = sum(1 for aircraft in test_fleet 
                        if fleet_results[f"{aircraft.aircraft_model}-{aircraft.msn}"][1].status == "yes")
    
    print(f"FAA AD 2025-23-53:")
    print(f"  - Affected: {faa_affected}/{len(test_fleet)} aircraft")
    print(f"  - Not Applicable: {len(test_fleet) - faa_affected}/{len(test_fleet)} aircraft")
    
    print(f"\nEASA AD 2025-0254:")
    print(f"  - Affected: {easa_affected}/{len(test_fleet)} aircraft")
    print(f"  - Excluded by modifications: {sum(1 for aircraft in test_fleet if fleet_results[f'{aircraft.aircraft_model}-{aircraft.msn}'][1].status == 'no')}")
    print(f"  - Not Applicable: {sum(1 for aircraft in test_fleet if fleet_results[f'{aircraft.aircraft_model}-{aircraft.msn}'][1].status == 'not applicable')}/{len(test_fleet)} aircraft")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()

