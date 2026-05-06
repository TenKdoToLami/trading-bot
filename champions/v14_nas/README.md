# 🏛️ V14.0 NAS "Elastic Brain"

The **V14 NAS** is a breakthrough in tactical architecture. It allows the genome to surgically grow or prune its own brain density based on market complexity.

---

## 🧬 Tactical Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Evolution** | `python tests/run_evolution_universal.py --version v14_nas --pop 100 --gen 100` |
| **Seeded Run** | `python tests/run_evolution_universal.py --version v14_nas --pop 500 --gen 100 --vault champions/v14_nas/vault` |
| **NAS Optimization** | `python tests/optimize_v14_nas.py` |

### 🔬 Diagnostics
| Goal | Command |
| :--- | :--- |
| **Full Audit** | `python tests/performance_audit.py champions/v14_nas/genome.json` |
| **X-Ray Analysis** | `python tests/genome_xray.py champions/v14_nas/genome.json` |
| **Vault Sweep** | `python tests/vault_sweep.py --vault champions/v14_nas/vault --promote --top 20` |

---

## 🧠 Neural Architecture Search (NAS)

V14 introduces **Active Slicing**, allowing the neural brains to find their own optimal size:

### 1. The Elastic Sentinel (`sentinel_dim`)
*   **Range**: 2 to 32 neurons.
*   **Role**: Learns the minimum number of neurons required to read market regimes. 
*   **Sparsity Penalty**: The fitness function penalizes "fat" brains (-0.05 per neuron). This forces the bot to only get smarter if it actually increases CAGR.

### 2. The Elastic Commander (`commander_dim`)
*   **Range**: 2 to 16 neurons.
*   **Role**: Dynamically adjusts the complexity of the defensive rotation (Cash/Gold/TLT).

### 3. Architecture Logic
*   The strategy stores **Master Weights** (32x32). 
*   The `sentinel_dim` gene acts as a "Slice" operator—the bot only loads the top-left section of the matrix. This allows intelligence to be "transferred" when the brain grows or shrinks.

---

## ⚙️ Key NAS Parameters
| Parameter | Range | Impact |
| :--- | :--- | :--- |
| `sentinel_dim` | 2 – 32 | Decision-making complexity (The "Generalist"). |
| `commander_dim` | 2 – 16 | Defensive split complexity (The "Specialist"). |
| `sparsity_penalty` | -0.05/neuron | Evolutionary pressure to stay efficient and avoid overfitting. |
