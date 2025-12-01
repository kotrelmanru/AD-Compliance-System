# AI Engineer Take-Home Assignment: AD Compliance System

## Overview

This project extracts and formalizes compliance rules from aviation Airworthiness Directives (ADs) and provides a machine-executable system to determine aircraft applicability.

## 📋 Deliverables

### 1. Extracted Rules in JSON Format

The applicability rules are stored in `ad_rules.json` with the following structure:

```json
{
  "ad_id": "FAA-2025-23-53",
  "issuing_authority": "FAA",
  "title": "McDonnell Douglas DC-10 and MD-11 Aircraft",
  "applicability_rules": {
    "aircraft_models": ["DC-10-10", "DC-10-10F", "MD-11", ...],
    "msn_constraints": {"type": "all"},
    "excluded_if_modifications": [],
    "required_modifications": []
  }
}
```

### 2. Python Code for Rule Evaluation

The system consists of three main modules:

- **`ad_compliance_schema.py`**: Pydantic models for type-safe rule representation
- **`ad_compliance_engine.py`**: Evaluation logic for checking aircraft against ADs
- **`test_ad_compliance.py`**: Test script for the 10 aircraft configurations

### 3. Test Results

| Aircraft Model | MSN   | Modifications               | FAA-2025-23-53 | EASA-2025-0254 |
|----------------|-------|-----------------------------|----------------|----------------|
| MD-11          | 48123 | None                        | **yes**        | not applicable |
| DC-10-30F      | 47890 | None                        | **yes**        | not applicable |
| Boeing 737-800 | 30123 | None                        | not applicable | not applicable |
| A320-214       | 5234  | None                        | not applicable | **yes**        |
| A320-232       | 6789  | mod 24591 (production)      | not applicable | **no**         |
| A320-214       | 7456  | SB A320-57-1089 Rev 04      | not applicable | **no**         |
| A321-111       | 8123  | None                        | not applicable | **yes**        |
| A321-112       | 364   | mod 24977 (production)      | not applicable | **no**         |
| A319-100       | 9234  | None                        | not applicable | not applicable |
| MD-10-10F      | 46234 | None                        | **yes**        | not applicable |

**Summary:**
- **FAA AD 2025-23-53**: Affects 3/10 aircraft (all DC-10/MD-10/MD-11 series)
- **EASA AD 2025-0254**: Affects 2/10 aircraft (A320-214 #5234, A321-111 #8123); 3 aircraft excluded by production modifications

### 4. Schema Design and Extraction Approach

## 🏗️ Schema Design

### Design Philosophy

The schema was designed with the following principles:

1. **Extensibility**: Support for future constraint types (flight hours, dates, etc.)
2. **Type Safety**: Pydantic models for validation and IDE support
3. **Readability**: Clear, self-documenting field names
4. **Database-Friendly**: JSON-serializable for easy storage
5. **Flexibility**: Handles multiple constraint types and edge cases

### Core Models

#### 1. `AirworthinessDirective`
Top-level model representing a complete AD with metadata and applicability rules.

```python
class AirworthinessDirective:
    ad_id: str                          # Unique identifier
    issuing_authority: str              # FAA, EASA, etc.
    title: Optional[str]
    effective_date: Optional[str]
    applicability_rules: ApplicabilityRules
    summary: Optional[str]
```

#### 2. `ApplicabilityRules`
Core logic for determining which aircraft are affected.

```python
class ApplicabilityRules:
    aircraft_models: List[str]                          # Required: affected models
    msn_constraints: Optional[MSNConstraint]            # Optional: MSN filtering
    excluded_if_modifications: List[ModificationConstraint]  # Exclusions
    required_modifications: List[ModificationConstraint]     # Requirements
    additional_constraints: Dict[str, Any]              # Future: hours, cycles
```

**Logic Flow:**
1. Check if aircraft model is in the list → if not, "not applicable"
2. Check MSN constraints → if doesn't match, "not applicable"
3. Check excluded modifications → if has any, "no" (excluded)
4. Check required modifications → if missing all, "no"
5. If all checks pass → "yes" (affected)

#### 3. `MSNConstraint`
Flexible MSN filtering supporting multiple constraint types.

```python
class MSNConstraint:
    type: MSNConstraintType  # "all", "range", "list"
    min_msn: Optional[int]   # For range-based
    max_msn: Optional[int]   # For range-based
    msn_list: Optional[List[int]]  # For list-based
```

**Examples:**
- Type "all": All MSNs valid (used for both ADs)
- Type "range": MSN between 1000-5000
- Type "list": MSN in [1234, 5678, 9012]

#### 4. `ModificationConstraint`
Handles the complexity of modification matching with aliases and fuzzy matching.

```python
class ModificationConstraint:
    mod_id: str                    # Primary identifier
    aliases: List[str]             # Alternative names
    description: Optional[str]     # Human-readable description
```

**Matching Logic:**
- Case-insensitive substring matching
- Supports multiple aliases (e.g., "SB A320-57-1089" matches "SBA320-57-1089")
- Handles revision variations (Rev 04, Rev 4, etc.)

#### 5. `AircraftConfiguration`
Represents a specific aircraft to be checked.

```python
class AircraftConfiguration:
    aircraft_model: str
    msn: int
    modifications: List[str]
    additional_info: Dict[str, Any]  # Future: hours, cycles, dates
```

#### 6. `ComplianceResult`
Output of the evaluation with detailed reasoning.

```python
class ComplianceResult:
    ad_id: str
    aircraft_model: str
    msn: int
    is_affected: bool
    status: str          # "yes", "no", "not applicable"
    reason: str          # Detailed explanation
```

## 🔍 Extraction Approach

### Step 1: Document Analysis

I used web search to access the official AD documents from EASA's Safety Publications Tool:
- FAA AD 2025-23-53: https://ad.easa.europa.eu/ad/US-2025-23-53
- EASA AD 2025-0254: https://ad.easa.europa.eu/ad/2025-0254

### Step 2: Rule Identification

For each AD, I extracted:

**FAA AD 2025-23-53:**
- **Affected Aircraft**: All DC-10 variants, MD-10 variants, and MD-11 variants
- **MSN Constraints**: None (all serial numbers)
- **Modifications**: No exclusions or requirements
- **Reasoning**: Broad applicability to entire aircraft families

**EASA AD 2025-0254:**
- **Affected Aircraft**: A320-2XX and A321-1XX families (specific variants)
- **MSN Constraints**: None (all serial numbers)
- **Excluded Modifications**:
  - mod 24591 (production) - structural modification at factory
  - SB A320-57-1089 (all revisions) - service bulletin addressing the issue
  - mod 24977 (production) - alternative structural modification
- **Reasoning**: Aircraft with these mods already have the fix incorporated

### Step 3: Schema Mapping

Mapped extracted information to the Pydantic schema:

```python
# Example: EASA AD modification exclusion
{
  "mod_id": "mod 24591",
  "aliases": ["24591", "modification 24591", "mod24591"],
  "description": "Production modification 24591 - if incorporated at production, AD does not apply"
}
```

### Step 4: Validation

The evaluation engine performs multi-stage validation:

1. **Model Check**: Quick rejection for non-applicable aircraft
2. **MSN Check**: Filters by serial number constraints
3. **Exclusion Check**: Identifies aircraft with exempting modifications
4. **Requirement Check**: Ensures required modifications are present
5. **Result Generation**: Provides detailed reasoning for each decision

## 🚀 Usage

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

```bash
python test_ad_compliance.py
```

### Using the Library

```python
from ad_compliance_schema import AircraftConfiguration
from ad_compliance_engine import ADComplianceEngine

# Initialize engine
engine = ADComplianceEngine("ad_rules.json")

# Create aircraft configuration
aircraft = AircraftConfiguration(
    aircraft_model="A320-214",
    msn=5234,
    modifications=[]
)

# Evaluate against all ADs
results = engine.evaluate_all(aircraft)

for result in results:
    print(f"{result.ad_id}: {result.status}")
    print(f"Reason: {result.reason}")
```

## 🎯 Key Features

### 1. Flexible Modification Matching
Handles various modification naming conventions:
- "mod 24591 (production)" matches "24591"
- "SB A320-57-1089 Rev 04" matches "A320-57-1089"
- Case-insensitive and whitespace-tolerant

### 2. Detailed Reasoning
Every decision includes step-by-step reasoning:
```
Model check: Aircraft model 'A320-214' is in the affected models list;
MSN check: MSN 5234 meets the constraints;
Excluded mods check: Aircraft does not have any excluded modifications;
Required mods check: No required modifications specified
```

### 3. Multiple Output Formats
- Console table for human readability
- JSON export for database storage
- Pydantic models for programmatic access

### 4. Extensible Design
Easy to add new constraint types:
- Flight hours/cycles thresholds
- Manufacturing date ranges
- Configuration-specific rules
- Geographic restrictions

## 📊 Complexity Handled

The system handles:
- ✅ Multiple aircraft model variants
- ✅ Production modifications vs. service bulletins
- ✅ Modification revision tracking
- ✅ Exclusion logic (has mod → not affected)
- ✅ Requirement logic (needs mod → affected only if has it)
- ✅ MSN range and list constraints
- ✅ Multiple ADs evaluated simultaneously
- ✅ Detailed audit trail for compliance decisions

## 🔮 Future Enhancements

The schema supports future additions without breaking changes:

1. **Time-based Constraints**
   ```json
   "additional_constraints": {
     "manufacturing_date_before": "2020-01-01",
     "flight_hours_exceeding": 50000
   }
   ```

2. **Complex Boolean Logic**
   ```json
   "excluded_if_modifications": [
     {"logic": "AND", "mods": ["mod1", "mod2"]},
     {"logic": "OR", "mods": ["mod3", "mod4"]}
   ]
   ```

3. **Geographic Restrictions**
   ```json
   "additional_constraints": {
     "operating_regions": ["EU", "US"]
   }
   ```

## 📝 Files Included

- `ad_compliance_schema.py` - Pydantic models and type definitions
- `ad_compliance_engine.py` - Evaluation logic and engine
- `test_ad_compliance.py` - Test script for 10 aircraft
- `ad_rules.json` - Extracted AD rules
- `test_results.json` - Detailed test results (generated)
- `requirements.txt` - Python dependencies
- `README.md` - This document

## 🏆 Design Decisions

### Why Pydantic?
- Type safety and validation
- Excellent IDE support
- Easy JSON serialization/deserialization
- Self-documenting code

### Why Separate Modification Constraints?
- Allows for complex matching logic
- Supports aliases and variations
- Extensible for future mod metadata

### Why Three-State Status?
- **"yes"**: Clearly affected, must comply
- **"no"**: Model matches but excluded (e.g., already fixed)
- **"not applicable"**: Model doesn't match at all

This distinction is crucial for compliance reporting and audit trails.

## 📧 Contact

For questions about this implementation or to discuss aviation compliance challenges, feel free to reach out!

---

**Note**: This implementation is based on publicly available AD information. In a production system, you would integrate with official aviation authority APIs and databases for real-time updates.

