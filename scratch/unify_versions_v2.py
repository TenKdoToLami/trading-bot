import os
import json
import glob

def unify_genomes():
    # Specific mapping to preserve architecture types
    v_map = [
        ("v1_manual", 1.0),
        ("v2", 2.0),
        ("v3", 3.0),
        ("v4_precision", 4.0),
        ("v5", 5.0),
        ("v6", 6.0),
        ("v7_deep_fluid", 7.2),
        ("v7_deep_binary", 7.1),
        ("v7_deep", 7.0),
        ("v8", 8.0),
        ("v9", 9.0)
    ]

    print("Starting Institutional Version Unification V2...")
    
    # Search in champions and vaults
    search_paths = [
        "champions/**/genome.json",
        "champions/**/vault/*.json"
    ]

    count = 0
    for pattern in search_paths:
        for file_path in glob.glob(pattern, recursive=True):
            try:
                path_lower = file_path.lower().replace("\\", "/")
                version = None
                
                # Search for the longest match first to catch specific sub-versions
                for key, val in v_map:
                    if key in path_lower:
                        version = val
                        break
                
                if version is None:
                    continue

                with open(file_path, 'r') as f:
                    genome = json.load(f)
                
                # Standardize to "version" key
                if genome.get("version") != version:
                    genome["version"] = version
                    if "Genome Version" in genome:
                        del genome["Genome Version"]
                    
                    with open(file_path, 'w') as f:
                        json.dump(genome, f, indent=4)
                    
                    print(f"  [FIXED] {file_path} -> {version}")
                    count += 1

            except Exception as e:
                print(f"  [ERROR] {file_path}: {e}")

    print(f"\nUnification Complete. {count} files updated.")

if __name__ == "__main__":
    unify_genomes()
