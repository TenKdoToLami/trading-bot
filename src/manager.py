import json

class BotManager:
    def __init__(self, db, engine):
        self.db = db
        self.engine = engine
        self.load_state()

    def load_state(self):
        self.panic_mode = int(self.db.get_state('panic_mode')) == 1
        self.days_in_regime = int(self.db.get_state('days_in_regime'))
        self.current_tier = int(self.db.get_state('current_tier'))
        self.base_lockout = int(self.db.get_state('base_lockout') or 0)

    def save_state(self):
        self.db.set_state('panic_mode', 1 if self.panic_mode else 0)
        self.db.set_state('days_in_regime', self.days_in_regime)
        self.db.set_state('current_tier', self.current_tier)
        self.db.set_state('base_lockout', self.base_lockout)

    def process_day(self, history):
        calc = self.engine.calculate_indicators(history)
        dna = self.engine.dna
        
        # 1. Update Regime State
        self.days_in_regime += 1
        new_panic_mode = self.panic_mode
        
        if self.panic_mode:
            # Recovery from Panic (Instant)
            if not calc['sma_triggered']:
                new_panic_mode = False
                self.days_in_regime = 0
        else:
            # Entering Panic (Has min_b_days delay)
            if calc['sma_triggered'] and self.days_in_regime >= dna.get('min_b_days', 10):
                new_panic_mode = True
                self.days_in_regime = 0
        
        self.panic_mode = new_panic_mode
        
        # 2. Update Tier State
        target_tier = calc['tier_p'] if self.panic_mode else calc['tier_b']
        
        # Base Lockout Logic (Persists as requested previously)
        if self.base_lockout > 0:
            self.base_lockout -= 1
            target_tier = self.current_tier
        
        # Immediate Switching (No Tier Lock)
        changed = False
        if self.current_tier == -1:
            self.current_tier = target_tier
            changed = True
        elif target_tier != self.current_tier:
            # Entering B0 Trigger Lockout
            if not self.panic_mode and target_tier == 0:
                self.base_lockout = dna.get('base_lockout_days', 10)
            
            self.current_tier = target_tier
            changed = True
            
        self.save_state()
        
        # 3. Get Final Allocation
        regime_label = "panic" if self.panic_mode else "bull"
        weights = self.engine.get_allocation(regime_label, self.current_tier)
        
        return {
            "regime": regime_label,
            "tier": self.current_tier,
            "weights": weights,
            "changed": changed
        }
