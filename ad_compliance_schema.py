"""
Airworthiness Directive (AD) Compliance Schema

This module defines Pydantic models for representing and validating
AD applicability rules extracted from regulatory documents.
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MSNConstraintType(str, Enum):
    """Types of MSN constraints"""
    RANGE = "range"  # MSN between min and max
    LIST = "list"    # MSN in specific list
    ALL = "all"      # All MSNs (no constraint)


class MSNConstraint(BaseModel):
    """
    Manufacturer Serial Number constraints
    
    Supports:
    - Range-based: MSN between min_msn and max_msn
    - List-based: MSN in msn_list
    - All: No MSN restrictions
    """
    type: MSNConstraintType
    min_msn: Optional[int] = None
    max_msn: Optional[int] = None
    msn_list: Optional[List[int]] = None
    
    def matches(self, msn: int) -> bool:
        """Check if given MSN matches this constraint"""
        if self.type == MSNConstraintType.ALL:
            return True
        elif self.type == MSNConstraintType.RANGE:
            if self.min_msn is not None and msn < self.min_msn:
                return False
            if self.max_msn is not None and msn > self.max_msn:
                return False
            return True
        elif self.type == MSNConstraintType.LIST:
            return msn in (self.msn_list or [])
        return False


class ModificationConstraint(BaseModel):
    """
    Modification/Service Bulletin constraint
    
    Can represent:
    - Production modifications (e.g., "mod 24591 (production)")
    - Service Bulletins (e.g., "SB A320-57-1089 Rev 04")
    - Configuration changes
    """
    mod_id: str = Field(description="Modification identifier")
    aliases: List[str] = Field(default_factory=list, description="Alternative names/versions")
    description: Optional[str] = None
    
    def matches(self, modification: str) -> bool:
        """Check if given modification string matches this constraint"""
        mod_lower = modification.lower().strip()
        if self.mod_id.lower() in mod_lower:
            return True
        for alias in self.aliases:
            if alias.lower() in mod_lower:
                return True
        return False


class ApplicabilityRules(BaseModel):
    """
    Core applicability rules for an AD
    
    Defines which aircraft are affected based on:
    - Aircraft models
    - MSN constraints
    - Required modifications (aircraft must have these)
    - Excluded modifications (aircraft with these are NOT affected)
    """
    aircraft_models: List[str] = Field(
        description="List of aircraft models affected by this AD"
    )
    
    msn_constraints: Optional[MSNConstraint] = Field(
        default=None,
        description="Manufacturer Serial Number constraints"
    )
    
    excluded_if_modifications: List[ModificationConstraint] = Field(
        default_factory=list,
        description="If aircraft has any of these mods, AD does NOT apply"
    )
    
    required_modifications: List[ModificationConstraint] = Field(
        default_factory=list,
        description="Aircraft must have at least one of these mods for AD to apply"
    )
    
    additional_constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional constraints (flight hours, cycles, dates, etc.)"
    )


class AirworthinessDirective(BaseModel):
    """
    Complete Airworthiness Directive representation
    
    Contains all information needed to determine if an aircraft
    is affected by this AD.
    """
    ad_id: str = Field(description="Unique AD identifier (e.g., 'FAA-2025-23-53')")
    issuing_authority: str = Field(description="FAA, EASA, etc.")
    title: Optional[str] = None
    effective_date: Optional[str] = None
    applicability_rules: ApplicabilityRules
    summary: Optional[str] = Field(
        default=None,
        description="Brief summary of what the AD addresses"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "ad_id": "FAA-2025-23-53",
                "issuing_authority": "FAA",
                "applicability_rules": {
                    "aircraft_models": ["MD-11", "MD-11F", "DC-10-30F"],
                    "msn_constraints": None,
                    "excluded_if_modifications": [],
                    "required_modifications": []
                }
            }
        }


class AircraftConfiguration(BaseModel):
    """
    Represents a specific aircraft configuration for compliance checking
    """
    aircraft_model: str
    msn: int = Field(description="Manufacturer Serial Number")
    modifications: List[str] = Field(
        default_factory=list,
        description="List of modifications applied to this aircraft"
    )
    additional_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional info like flight hours, cycles, etc."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "aircraft_model": "A320-214",
                "msn": 5234,
                "modifications": ["SB A320-57-1089 Rev 04"],
                "additional_info": {}
            }
        }


class ComplianceResult(BaseModel):
    """
    Result of checking an aircraft against an AD
    """
    ad_id: str
    aircraft_model: str
    msn: int
    is_affected: bool
    status: str = Field(description="'yes', 'no', or 'not applicable'")
    reason: str = Field(description="Explanation of why this status was determined")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ad_id": "FAA-2025-23-53",
                "aircraft_model": "MD-11",
                "msn": 48123,
                "is_affected": True,
                "status": "yes",
                "reason": "Aircraft model MD-11 is in affected models list"
            }
        }

