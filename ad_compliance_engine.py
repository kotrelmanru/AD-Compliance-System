"""
Airworthiness Directive Compliance Evaluation Engine

This module implements the logic to evaluate aircraft configurations
against AD applicability rules and determine compliance status.
"""

import json
from typing import List, Dict, Tuple
from pathlib import Path
from ad_compliance_schema import (
    AirworthinessDirective,
    AircraftConfiguration,
    ComplianceResult,
    MSNConstraint,
    ModificationConstraint
)


class ADComplianceEngine:
    """
    Engine for evaluating aircraft configurations against AD rules
    """
    
    def __init__(self, ad_rules_path: str = "ad_rules.json"):
        """
        Initialize the engine with AD rules from JSON file
        
        Args:
            ad_rules_path: Path to JSON file containing AD rules
        """
        self.ads: List[AirworthinessDirective] = []
        self.load_rules(ad_rules_path)
    
    def load_rules(self, rules_path: str):
        """Load AD rules from JSON file"""
        with open(rules_path, 'r') as f:
            rules_data = json.load(f)
        
        for ad_data in rules_data:
            # Convert modification dicts to ModificationConstraint objects
            if 'excluded_if_modifications' in ad_data['applicability_rules']:
                ad_data['applicability_rules']['excluded_if_modifications'] = [
                    ModificationConstraint(**mod) 
                    for mod in ad_data['applicability_rules']['excluded_if_modifications']
                ]
            
            if 'required_modifications' in ad_data['applicability_rules']:
                ad_data['applicability_rules']['required_modifications'] = [
                    ModificationConstraint(**mod)
                    for mod in ad_data['applicability_rules']['required_modifications']
                ]
            
            # Convert MSN constraints
            if 'msn_constraints' in ad_data['applicability_rules'] and ad_data['applicability_rules']['msn_constraints']:
                ad_data['applicability_rules']['msn_constraints'] = MSNConstraint(
                    **ad_data['applicability_rules']['msn_constraints']
                )
            
            ad = AirworthinessDirective(**ad_data)
            self.ads.append(ad)
    
    def check_aircraft_model(self, aircraft: AircraftConfiguration, ad: AirworthinessDirective) -> Tuple[bool, str]:
        """
        Check if aircraft model matches AD applicability
        
        Returns:
            (matches: bool, reason: str)
        """
        if aircraft.aircraft_model not in ad.applicability_rules.aircraft_models:
            return False, f"Aircraft model '{aircraft.aircraft_model}' is not in the affected models list"
        return True, f"Aircraft model '{aircraft.aircraft_model}' is in the affected models list"
    
    def check_msn_constraints(self, aircraft: AircraftConfiguration, ad: AirworthinessDirective) -> Tuple[bool, str]:
        """
        Check if aircraft MSN meets AD constraints
        
        Returns:
            (matches: bool, reason: str)
        """
        if ad.applicability_rules.msn_constraints is None:
            return True, "No MSN constraints specified"
        
        if ad.applicability_rules.msn_constraints.matches(aircraft.msn):
            return True, f"MSN {aircraft.msn} meets the constraints"
        else:
            return False, f"MSN {aircraft.msn} does not meet the constraints"
    
    def check_excluded_modifications(self, aircraft: AircraftConfiguration, ad: AirworthinessDirective) -> Tuple[bool, str]:
        """
        Check if aircraft has any modifications that exclude it from AD
        
        Returns:
            (is_excluded: bool, reason: str)
        """
        for excluded_mod in ad.applicability_rules.excluded_if_modifications:
            for aircraft_mod in aircraft.modifications:
                if excluded_mod.matches(aircraft_mod):
                    return True, f"Aircraft has excluded modification: {excluded_mod.mod_id} (matched: {aircraft_mod})"
        
        if ad.applicability_rules.excluded_if_modifications:
            return False, "Aircraft does not have any excluded modifications"
        return False, "No excluded modifications specified"
    
    def check_required_modifications(self, aircraft: AircraftConfiguration, ad: AirworthinessDirective) -> Tuple[bool, str]:
        """
        Check if aircraft has required modifications for AD to apply
        
        Returns:
            (has_required: bool, reason: str)
        """
        if not ad.applicability_rules.required_modifications:
            return True, "No required modifications specified"
        
        for required_mod in ad.applicability_rules.required_modifications:
            for aircraft_mod in aircraft.modifications:
                if required_mod.matches(aircraft_mod):
                    return True, f"Aircraft has required modification: {required_mod.mod_id}"
        
        return False, "Aircraft does not have any of the required modifications"
    
    def evaluate(self, aircraft: AircraftConfiguration, ad: AirworthinessDirective) -> ComplianceResult:
        """
        Evaluate a single aircraft against a single AD
        
        Returns:
            ComplianceResult with status and detailed reasoning
        """
        reasons = []
        
        # Step 1: Check aircraft model
        model_matches, model_reason = self.check_aircraft_model(aircraft, ad)
        reasons.append(f"Model check: {model_reason}")
        
        if not model_matches:
            return ComplianceResult(
                ad_id=ad.ad_id,
                aircraft_model=aircraft.aircraft_model,
                msn=aircraft.msn,
                is_affected=False,
                status="not applicable",
                reason="; ".join(reasons)
            )
        
        # Step 2: Check MSN constraints
        msn_matches, msn_reason = self.check_msn_constraints(aircraft, ad)
        reasons.append(f"MSN check: {msn_reason}")
        
        if not msn_matches:
            return ComplianceResult(
                ad_id=ad.ad_id,
                aircraft_model=aircraft.aircraft_model,
                msn=aircraft.msn,
                is_affected=False,
                status="not applicable",
                reason="; ".join(reasons)
            )
        
        # Step 3: Check excluded modifications
        is_excluded, excluded_reason = self.check_excluded_modifications(aircraft, ad)
        reasons.append(f"Excluded mods check: {excluded_reason}")
        
        if is_excluded:
            return ComplianceResult(
                ad_id=ad.ad_id,
                aircraft_model=aircraft.aircraft_model,
                msn=aircraft.msn,
                is_affected=False,
                status="no",
                reason="; ".join(reasons)
            )
        
        # Step 4: Check required modifications
        has_required, required_reason = self.check_required_modifications(aircraft, ad)
        reasons.append(f"Required mods check: {required_reason}")
        
        if not has_required:
            return ComplianceResult(
                ad_id=ad.ad_id,
                aircraft_model=aircraft.aircraft_model,
                msn=aircraft.msn,
                is_affected=False,
                status="no",
                reason="; ".join(reasons)
            )
        
        # All checks passed - aircraft IS affected by this AD
        return ComplianceResult(
            ad_id=ad.ad_id,
            aircraft_model=aircraft.aircraft_model,
            msn=aircraft.msn,
            is_affected=True,
            status="yes",
            reason="; ".join(reasons)
        )
    
    def evaluate_all(self, aircraft: AircraftConfiguration) -> List[ComplianceResult]:
        """
        Evaluate a single aircraft against all loaded ADs
        
        Returns:
            List of ComplianceResults, one for each AD
        """
        results = []
        for ad in self.ads:
            result = self.evaluate(aircraft, ad)
            results.append(result)
        return results
    
    def evaluate_fleet(self, fleet: List[AircraftConfiguration]) -> Dict[str, List[ComplianceResult]]:
        """
        Evaluate multiple aircraft against all loaded ADs
        
        Returns:
            Dict mapping aircraft identifier to list of compliance results
        """
        fleet_results = {}
        for aircraft in fleet:
            aircraft_id = f"{aircraft.aircraft_model}-{aircraft.msn}"
            fleet_results[aircraft_id] = self.evaluate_all(aircraft)
        return fleet_results


def format_results_table(results: Dict[str, List[ComplianceResult]]) -> str:
    """
    Format compliance results as a readable table
    
    Args:
        results: Dict from evaluate_fleet()
    
    Returns:
        Formatted table string
    """
    # Extract unique AD IDs
    ad_ids = []
    if results:
        first_results = next(iter(results.values()))
        ad_ids = [r.ad_id for r in first_results]
    
    # Build table header
    header = ["Aircraft Model", "MSN", "Modifications"] + ad_ids
    
    # Calculate column widths
    col_widths = [len(h) for h in header]
    
    # Build table rows
    rows = []
    for aircraft_id, compliance_results in results.items():
        # Extract aircraft info from first result
        result = compliance_results[0]
        
        # Get modifications list (reconstruct from stored data)
        mods_str = "None"
        if hasattr(result, 'modifications') and result.modifications:
            mods_str = ", ".join(result.modifications)
        
        row = [
            result.aircraft_model,
            str(result.msn),
            mods_str
        ]
        
        # Add compliance status for each AD
        for r in compliance_results:
            row.append(r.status)
        
        rows.append(row)
        
        # Update column widths
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))
    
    # Format table
    separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    header_row = "|" + "|".join([f" {h:<{col_widths[i]}} " for i, h in enumerate(header)]) + "|"
    
    table = [separator, header_row, separator]
    
    for row in rows:
        row_str = "|" + "|".join([f" {cell:<{col_widths[i]}} " for i, cell in enumerate(row)]) + "|"
        table.append(row_str)
    
    table.append(separator)
    
    return "\n".join(table)


if __name__ == "__main__":
    # Example usage
    engine = ADComplianceEngine("ad_rules.json")
    
    # Test aircraft
    test_aircraft = AircraftConfiguration(
        aircraft_model="MD-11",
        msn=48123,
        modifications=[]
    )
    
    results = engine.evaluate_all(test_aircraft)
    
    print(f"\nEvaluation results for {test_aircraft.aircraft_model} MSN {test_aircraft.msn}:")
    print("-" * 80)
    for result in results:
        print(f"\nAD: {result.ad_id}")
        print(f"Status: {result.status}")
        print(f"Affected: {result.is_affected}")
        print(f"Reason: {result.reason}")

