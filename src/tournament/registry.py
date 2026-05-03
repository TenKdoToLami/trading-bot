"""
Central registry for strategy versions.
Allows for polymorphic instantiation of strategies based on version identifiers.
"""

import numpy as np
from typing import Dict, Type, Any

# Dictionary mapping version IDs (strings or floats) to Strategy classes
_STRATEGY_REGISTRY: Dict[Any, Type] = {}

def register_strategy(version_id: Any):
    """
    Decorator to register a strategy class with one or more version identifiers.
    """
    def decorator(cls: Type):
        if isinstance(version_id, list):
            for vid in version_id:
                _STRATEGY_REGISTRY[vid] = cls
        else:
            _STRATEGY_REGISTRY[version_id] = cls
        
        # Store the primary version_id on the class for reference
        cls.VERSION_ID = version_id[0] if isinstance(version_id, list) else version_id
        return cls
    return decorator

def structural_detect(genome: dict) -> Any:
    """
    Detects the version of a genome by analyzing its structure.
    Used for legacy genomes that lack a 'version' key.
    """
    if "brain_a" in genome: return "v10_alpha"
    if "hysteresis" in genome: return "v9_confidence"
    if "layers" in genome:
        # Distinguish V7 variants by output layer shape
        try:
            out_w = np.array(genome["layers"][-1]["w"])
            if out_w.shape[1] == 2: return "v7_deep_binary"
            if out_w.shape[1] == 1: return "v7_deep_fluid"
        except: pass
        return "v7_deep"
    if "brains" in genome:
        b = genome["brains"]
        if "cash" in b or "1x" in b: return "v6_balancer"
        if "3x" in b: return "v2_multi"
    if "sniper" in genome: return "v5_sniper"
    if "panic" in genome and "bull" in genome:
        # V3 and V4 both have panic/bull, but V4 is 3-state
        # Usually V4 has version=4.0, but if missing:
        if "lookbacks" in genome["panic"]: return "v4_precision"
        return "v3_precision"
    if "panic_weights" in genome: return "v1_classic"
    if "bounds_p" in genome: return "v1_manual"
    return None

def discover_all_strategies():
    """
    Dynamically imports all modules in the 'strategies' directory.
    This ensures that the @register_strategy decorators are executed.
    """
    import os
    import importlib
    import sys
    
    # Ensure project root is in path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    strategies_dir = os.path.join(project_root, "strategies")
    if not os.path.exists(strategies_dir):
        return

    for f in os.listdir(strategies_dir):
        if f.endswith(".py") and not f.startswith("_") and f != "base.py":
            module_name = f"strategies.{f[:-3]}"
            try:
                importlib.import_module(module_name)
            except Exception as e:
                # Silently skip modules that fail to load or aren't strategy plugins
                pass

def get_strategy_class(version_id: Any, genome: dict = None) -> Type:
    """
    Returns the strategy class associated with the given version_id.
    If version_id is missing/None, uses structural detection on the genome.
    """
    if not _STRATEGY_REGISTRY:
        discover_all_strategies()

    # 1. Try direct lookup
    cls = _STRATEGY_REGISTRY.get(version_id)
    if cls:
        return cls
        
    # 2. Try structural detection if genome provided
    if genome:
        vid = structural_detect(genome)
        cls = _STRATEGY_REGISTRY.get(vid)
        if cls: return cls

    return None
