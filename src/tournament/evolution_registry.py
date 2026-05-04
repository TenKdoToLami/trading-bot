"""
Evolution Registry — Unified Evolution Engine Management.
Allows for dynamic selection of evolution strategies.
"""

import os
import importlib
from typing import Dict, Type, Any, List, Optional

_EVO_REGISTRY: Dict[str, Type] = {}

def register_evolution(version_id: str):
    """Decorator to register an evolution engine class."""
    def decorator(cls):
        _EVO_REGISTRY[version_id] = cls
        return cls
    return decorator

def discover_evolution_engines():
    """Dynamically imports all evolution modules in src/tournament/."""
    import sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    tournament_dir = os.path.join(project_root, "src", "tournament")
    print(f"  [DEBUG] Scanning for evolution engines in: {tournament_dir}")
    
    if not os.path.exists(tournament_dir):
        print(f"  [ERROR] Tournament directory not found: {tournament_dir}")
        return

    for f in os.listdir(tournament_dir):
        if f.startswith("evolution_v") and f.endswith(".py"):
            module_name = f"src.tournament.{f[:-3]}"
            try:
                importlib.import_module(module_name)
            except Exception as e:
                print(f"  [WARN] Failed to import evolution engine {module_name}: {e}")
                import traceback
                traceback.print_exc()

def get_evolution_engine(version_id: str) -> Optional[Type]:
    """Returns the evolution engine class for a given version."""
    if not _EVO_REGISTRY:
        discover_evolution_engines()
    return _EVO_REGISTRY.get(version_id)

def get_all_evo_versions() -> List[str]:
    if not _EVO_REGISTRY:
        discover_evolution_engines()
    return sorted(list(_EVO_REGISTRY.keys()))
