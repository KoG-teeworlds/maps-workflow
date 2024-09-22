import numpy as np

from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleException, RuleViolation


class Exist(BaseRule):
    def evaluate(self):
        violations = []
        expected_tile = self.params['expected_tile']
        found_tile = []

        has_expected_layer = hasattr(self.params, 'expected_layer')
        for group in self.map_file.groups:
            for layer in group.layers:
                if layer.kind() != "Tiles":
                    continue

                for tile_layer in layer.tiles:
                    tile_layer_np = np.array(tile_layer)
                    matching_indices = np.where(tile_layer_np == expected_tile)

                    for h, w in zip(*matching_indices):
                        found_tile.append([tile_layer, h, w])

                        if has_expected_layer and layer.name != self.params['expected_layer']:
                            violations.append(RuleViolation(
                                message=f"Found tile \"{self.params['humanized']}\" at position ({h}, {w}) "
                                        f"in layer \"{layer.name}\" instead of \"{self.params['expected_layer']}\" layer.",
                                errors=[]
                            ))

        if len(found_tile) < 1:
            raise RuleException(message=f"Expected \"{self.params['humanized']}\" is not on the map at all")

        if hasattr(self.params, 'min_occurances'):
            if len(found_tile) < self.params['min_occurances']:
                raise RuleException(message=f"Expected \"{self.params['humanized']}\" to be atleast {self.params['min_occurances']} on the map.")

        if hasattr(self.params, 'max_occurances'):
            if len(found_tile) > self.params['max_occurances']:
                raise RuleException(message=f"Expected \"{self.params['humanized']}\" to be max {self.params['max_occurances']} on the map.")

        return violations
    
    def explain(self):
        return ["has_tile", "in", self.params['expected_tile']]
