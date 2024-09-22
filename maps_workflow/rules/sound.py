import hashlib
from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleViolation


class Valid(BaseRule):
    def evaluate(self):
        violations = []
        for sound in self.map_file.sounds:
            print(sound.name)
            data_str = str(sound.data).encode('utf-8')
            sha512_hash = hashlib.sha512()
            sha512_hash.update(data_str)
            print(sha512_hash.hexdigest())
    
    def explain(self):
        return ["setting", "in", None]
