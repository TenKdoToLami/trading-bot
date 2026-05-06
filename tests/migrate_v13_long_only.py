import json
import os
import numpy as np
from copy import deepcopy

TARGET_VERSION = "v13_moe_full"
VAULT_DIR = f"champions/{TARGET_VERSION}/vault"
GENOME_PATH = f"champions/{TARGET_VERSION}/genome.json"

def migrate_genome(path):
    if not os.path.exists(path):
        return
    
    print(f"  [MIGRATE] {path}")
    with open(path, 'r') as f:
        genome = json.load(f)
    
    # 1. Strip Assassin Expert
    if 'assassin_expert' in genome:
        del genome['assassin_expert']
    
    # 2. Refactor Sentinel (3 outputs -> 2 outputs)
    # Authority 0: Bull, Authority 1: Bear, Authority 2: Assassin (Delete this)
    sentinel = genome.get('sentinel')
    if sentinel:
        out_w = np.array(sentinel['out_w'])
        out_b = np.array(sentinel['out_b'])
        
        # Keep only the first 2 rows (Bull, Bear)
        if out_w.shape[1] == 3:
            sentinel['out_w'] = out_w[:, :2].tolist()
            sentinel['out_b'] = out_b[:2].tolist()
            print(f"    - Refactored Sentinel Authority: 3 -> 2")
            
    # 3. Update version
    genome['version'] = 13.8
    
    with open(path, 'w') as f:
        json.dump(genome, f, indent=4)

def run_migration():
    print("=== V13 MOE LONG-ONLY MIGRATION ===")
    
    # 1. Migrate active champion
    migrate_genome(GENOME_PATH)
    
    # 2. Migrate vault
    if os.path.exists(VAULT_DIR):
        for f_name in os.listdir(VAULT_DIR):
            if f_name.endswith('.json'):
                migrate_genome(os.path.join(VAULT_DIR, f_name))
                
    print("\n[SUCCESS] All genomes migrated to Long-Only architecture.")

if __name__ == "__main__":
    run_migration()
