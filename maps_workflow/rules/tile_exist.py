from twmap import Map
import numpy as np

from maps_workflow.exceptions import RuleException, RuleViolation


def tile_exist(raw_file, tw_map: Map, params):
    violations = []
    expected_tile = params['expected_tile']
    found_tile = []

    has_expected_layer = hasattr(params, 'expected_layer')
    for group in tw_map.groups:
        for layer in group.layers:
            if layer.kind() != "Tiles":
                continue

            for tile_layer in layer.tiles:
                tile_layer_np = np.array(tile_layer)
                matching_indices = np.where(tile_layer_np == expected_tile)

                for h, w in zip(*matching_indices):
                    found_tile.append([tile_layer, h, w])

                    if has_expected_layer and layer.name != params['expected_layer']:
                        violations.append(RuleViolation(
                            message=f"Found tile \"{params['humanized']}\" at position ({h}, {w}) "
                                    f"in layer \"{layer.name}\" instead of \"{params['expected_layer']}\" layer.",
                            errors=[]
                        ))

    if len(found_tile) < 1:
        raise RuleException(message=f"Expected \"{params['humanized']}\" is not on the map at all")

    if hasattr(params, 'min_occurances'):
        if len(found_tile) < params['min_occurances']:
            raise RuleException(message=f"Expected \"{params['humanized']}\" to be atleast {params['min_occurances']} on the map.")

    if hasattr(params, 'max_occurances'):
        if len(found_tile) > params['max_occurances']:
            raise RuleException(message=f"Expected \"{params['humanized']}\" to be max {params['max_occurances']} on the map.")

    return violations
