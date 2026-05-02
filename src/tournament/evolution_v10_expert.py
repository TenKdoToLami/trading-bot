import os
import json
import random
import numpy as np
import concurrent.futures
from copy import deepcopy
from tqdm import tqdm
from strategies.genome_v10_expert import GenomeV10Expert
from src.tournament.runner import TournamentRunner

class EvolutionV10Expert:
    """
    Genetic Algorithm Engine for Model V10 Expert Ensemble.
    Optimizes weights for the Bull Brain, Bear Brain, and MixMaster Brain.
    """
    
    def __init__(self, data_path, profile_path, population_size=100, generations=50, mutation_rate=0.2):
        self.data_path = data_path
        self.profile_path = profile_path
        self.pop_size = population_size
        self.generations = generations
        self.mut_rate = mutation_rate
        
        # Load profile to determine DNA structure
        with open(profile_path, 'r') as f:
            self.profile_data = json.load(f)['profiles']
        self.expert_keys = sorted(list(self.profile_data.keys()))
        self.num_experts = len(self.expert_keys)
        
        self.population = [self._create_random_genome() for _ in range(self.pop_size)]
        self.best_genome = None
        self.best_fitness = -float('inf')

    def _create_random_genome(self):
        # Brain A (Bull): Initialize with POSITIVE weights (0.0 to 1.0)
        # This ensures the bot starts by 'trusting' bullish signals
        w_a = np.random.uniform(0, 1, (self.num_experts, 1)).tolist()
        
        # Brain B (Bear): Standard initialization (-1 to 1)
        w_b = np.random.uniform(-1, 1, (self.num_experts, 1)).tolist()
        
        # Brain C (MixMaster): Inputs [Bull, Bear, Vol] -> [Cash, 1x, 2x, 3x]
        w_c = np.random.uniform(-1, 1, (3, 4)).tolist()
        
        # Bias MixMaster towards 1x (Index 1) instead of Cash (Index 0)
        b_c = [-1.0, 1.0, 0.0, -1.0] # Initial bias to favor 1x SPY
        
        return {
            'brain_a': {
                'w': w_a,
                'b': [0.0]
            },
            'brain_b': {
                'w': w_b,
                'b': [0.0]
            },
            'brain_c': {
                'w': w_c,
                'b': b_c
            },
            'overrides': {
                'bear_veto_threshold': random.uniform(0.7, 0.95)
            }
        }

    def _mutate(self, genome):
        new_genome = deepcopy(genome)
        
        def _mutate_matrix(m):
            m = np.array(m)
            mask = np.random.rand(*m.shape) < self.mut_rate
            m[mask] += np.random.normal(0, 0.1, m[mask].shape)
            return m.tolist()
            
        # Mutate Brains
        new_genome['brain_a']['w'] = _mutate_matrix(new_genome['brain_a']['w'])
        new_genome['brain_b']['w'] = _mutate_matrix(new_genome['brain_b']['w'])
        new_genome['brain_c']['w'] = _mutate_matrix(new_genome['brain_c']['w'])
        
        # Mutate Override
        if random.random() < self.mut_rate:
            new_genome['overrides']['bear_veto_threshold'] += random.normalvariate(0, 0.05)
            new_genome['overrides']['bear_veto_threshold'] = max(0.1, min(0.99, new_genome['overrides']['bear_veto_threshold']))
            
        return new_genome

    def _evaluate(self, genome):
        import sys
        import os
        from contextlib import redirect_stdout
        
        strategy = GenomeV10Expert(genome=genome, profile_path=self.profile_path)
        
        # Silence the runner's print statements
        with open(os.devnull, 'w') as fnull:
            with redirect_stdout(fnull):
                runner = TournamentRunner()
                runner.start_date = "1993-01-01"
                runner.load_data() 
                results = runner._run_set([strategy])
        
        # Extract metrics
        if not results:
            return -999, {"cagr": 0, "max_dd": 0, "avg_leverage": 0}, genome
            
        res = list(results.values())[0]
        metrics = res['metrics']
        cagr_pct = metrics['cagr'] * 100
        dd_pct = abs(metrics['max_dd']) * 100
        trades = metrics['num_rebalances']
        
        # --- V9 STYLE FITNESS LOGIC ---
        # CAGR % - (MaxDD % * 0.15)
        fitness = cagr_pct - (dd_pct * 0.15)
        
        # Safety / Activity Hard Penalties
        if dd_pct >= 95.0: 
            fitness -= 1000
        if trades == 0:
            fitness -= 2000 
            
        return fitness, metrics, genome

    def run(self, vault_path):
        os.makedirs(vault_path, exist_ok=True)
        print(f"{'Gen':<5} | {'Fitness':<10} | {'CAGR':<10} | {'Max DD':<10} | {'Veto':<6}")
        print("-" * 55)
        
        for gen in range(self.generations):
            # Parallel Evaluation
            with concurrent.futures.ProcessPoolExecutor() as executor:
                futures = [executor.submit(self._evaluate, g) for g in self.population]
                scored_pop = []
                for f in tqdm(concurrent.futures.as_completed(futures), total=self.pop_size, desc=f"Gen {gen+1}", leave=False):
                    try:
                        fitness, stats, genome = f.result()
                        scored_pop.append((fitness, stats, genome))
                    except Exception as e:
                        print(f"\nWorker Error: {e}")
            
            # Sort by fitness
            scored_pop.sort(key=lambda x: x[0], reverse=True)
            
            # Keep track of best
            best_fitness, best_stats, best_genome = scored_pop[0]
            
            if best_fitness > self.best_fitness:
                self.best_fitness = best_fitness
                self.best_genome = best_genome
                
                # BUNDLE PROFILES: Ensure the genome carries its indicators with it
                self.best_genome['indicator_profiles'] = self.profile_data
                
                # Save New Champion to Vault
                cagr_str = f"{best_stats['cagr']*100:.1f}"
                filename = f"v10_fit{best_fitness:.1f}_cagr{cagr_str}.json"
                with open(os.path.join(vault_path, filename), 'w') as f:
                    json.dump(self.best_genome, f, indent=4)
                
                # Also update the main genome.json for the champion folder
                with open(os.path.join(os.path.dirname(vault_path), "genome.json"), 'w') as f:
                    json.dump(self.best_genome, f, indent=4)

            # Print clean summary
            veto = best_genome['overrides']['bear_veto_threshold']
            print(f"{gen+1:<5} | {best_fitness:<10.2f} | {best_stats['cagr']:>9.2%} | {best_stats['max_dd']:>9.2%} | {veto:.2f}")
            
            # Selection & Breeding (Keep top 20%)
            new_pop = [scored_pop[i][2] for i in range(self.pop_size // 5)]
            
            # Fill the rest with mutations
            while len(new_pop) < self.pop_size:
                parent = random.choice(new_pop[:10])
                new_pop.append(self._mutate(parent))
                
            self.population = new_pop

        print(f"\nEvolution Complete. Best Fitness: {self.best_fitness:.2f}")
