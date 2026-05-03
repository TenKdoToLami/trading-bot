"""
Genome Schemas — Type-safe definitions for Strategy Genomes.
Uses dataclasses for compatibility without external dependencies.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

def from_dict(cls, data):
    """Helper to instantiate dataclasses from dictionaries with nesting."""
    if data is None: return None
    field_types = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    kwargs = {}
    for name, value in data.items():
        if name in field_types:
            ftype = field_types[name]
            # Handle nested dataclasses
            if hasattr(ftype, "__dataclass_fields__"):
                kwargs[name] = from_dict(ftype, value)
            # Handle List of dataclasses (simplified)
            elif str(ftype).startswith("typing.List") or str(ftype).startswith("list"):
                # We assume if it's a list of dicts, it might be nested
                kwargs[name] = value 
            else:
                kwargs[name] = value
    return cls(**kwargs)

@dataclass
class BrainSchema:
    w: Dict[str, float] = field(default_factory=dict)
    a: Dict[str, bool] = field(default_factory=dict)
    t: float = 0.0
    lookbacks: Dict[str, float] = field(default_factory=dict)

@dataclass
class V4Genome:
    panic: BrainSchema
    bull: BrainSchema
    lock_days: int = 0
    version: str = "v4_precision"

@dataclass
class V6Brain:
    w: Dict[str, float] = field(default_factory=dict)
    a: Dict[str, bool] = field(default_factory=dict)

@dataclass
class V6Genome:
    brains: Dict[str, V6Brain]
    lookbacks: Dict[str, float]
    temp: float = 1.0
    lock_days: int = 2
    version: str = "v6_balancer"

@dataclass
class V2Genome:
    panic: Dict[str, float]
    bull: Dict[str, float]
    version: str = "v2_multi"
    # Note: V2 structure is slightly different, but this serves as a baseline
