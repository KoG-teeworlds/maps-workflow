from twmap import Map

from maps_workflow.exceptions import RuleException, RuleViolation


def tile_exist(raw_file, tw_map: Map, params):
    violations = []
    expected_tile = params['expected_tile']
    found_tile = []

    for group in tw_map.groups:
        for layer in group.layers:
            if layer.kind() == "Tiles":
                for tile_layer in layer.tiles:
                    height, width = tile_layer.shape
                    for h in range(height):
                        for w in range(width):
                            tile = tile_layer[(h, w)]
                            if tile == expected_tile:
                                found_tile.append([tile_layer, h, w])
                                if hasattr(params, 'expected_layer'):
                                    if layer.name != params['expected_layer']:
                                        violations.append(RuleViolation(message=f"Found tile \"{params['humanized']}\" at position ({h}, {w}) in layer \"{layer.name}\" instead of \"{params['expected_layer']}\" layer.", errors=[]))

    if len(found_tile) < 1:
        raise RuleException(message=f"Expected \"{params['humanized']}\" is not on the map at all")

    if hasattr(params, 'min_occurances'):
        if len(found_tile) < params['min_occurances']:
            raise RuleException(message=f"Expected \"{params['humanized']}\" to be atleast {params['min_occurances']} on the map.")

    if hasattr(params, 'max_occurances'):
        if len(found_tile) > params['max_occurances']:
            raise RuleException(message=f"Expected \"{params['humanized']}\" to be max {params['max_occurances']} on the map.")

    return violations
