from typing import Optional
import numpy as np
from pydantic import BaseModel, PositiveInt

from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleException, RuleViolation


class ExistParams(BaseModel):
    expected_tile: int
    humanized: str
    expected_layer: Optional[str] = None
    min_occurances: Optional[PositiveInt] = None
    max_occurances: Optional[PositiveInt] = None

class Exist(BaseRule):
    params: ExistParams

    def get_params_model(self):
        return ExistParams

    def evaluate(self):
        violations = []
        found_tile = []

        for group in self.map_file.groups:
            for layer in group.layers:
                if layer.kind() != "Tiles":
                    continue

                for tile_layer in layer.tiles:
                    tile_layer_np = np.array(tile_layer)
                    matching_indices = np.where(tile_layer_np == self.params.expected_tile)

                    for h, w in zip(*matching_indices):
                        found_tile.append([tile_layer, h, w])

                        if self.params.expected_layer and layer.name != self.params.expected_layer:
                            violations.append(RuleViolation(
                                message=f"Found tile \"{self.params.humanized}\" at position ({h}, {w}) "
                                        f"in layer \"{layer.name}\" instead of \"{self.params.expected_layer}\" layer.",
                                errors=[]
                            ))

        if len(found_tile) < 1:
            raise RuleException(message=f"Expected \"{self.params.humanized}\" is not on the map at all")

        if self.params.min_occurances:
            if len(found_tile) < self.params.min_occurances:
                raise RuleException(message=f"Expected \"{self.params.humanized}\" to be atleast {self.params.min_occurances} on the map.")

        if self.params.max_occurances:
            if len(found_tile) > self.params.max_occurances:
                raise RuleException(message=f"Expected \"{self.params.humanized}\" to be max {self.params.max_occurances} on the map.")

        return violations
    
    def explain(self):
        return ["has_tile", "in", self.params['expected_tile']]
