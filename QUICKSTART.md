# Quick Start Guide

## Installation

```bash
# Clone/navigate to project directory
cd /path/to/iseng

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Run Tests

```bash
python test_ad_compliance.py
```

## Use as Library

```python
from ad_compliance_schema import AircraftConfiguration
from ad_compliance_engine import ADComplianceEngine

# Initialize engine
engine = ADComplianceEngine("ad_rules.json")

# Define aircraft
aircraft = AircraftConfiguration(
    aircraft_model="A320-214",
    msn=5234,
    modifications=[]
)

# Evaluate against all ADs
results = engine.evaluate_all(aircraft)

# Print results
for result in results:
    print(f"{result.ad_id}: {result.status}")
    print(f"Reason: {result.reason}\n")
```

## Files

- `ad_rules.json` - AD rules database
- `ad_compliance_schema.py` - Pydantic models
- `ad_compliance_engine.py` - Evaluation engine
- `test_ad_compliance.py` - Test script
- `README.md` - Full documentation
- `SOLUTION_SUMMARY.md` - Solution overview

## Output

```
Aircraft: A320-214 | MSN: 5234
FAA-2025-23-53: not applicable
EASA-2025-0254: yes (affected)
```

