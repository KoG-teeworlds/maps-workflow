from twmap import Map

def tile_exist(tw_map: Map, params):
    expected_tile = params['expected_tile']
    for layer in tw_map.game_layer().tiles:
        height, width = layer.shape
        for h in range(height):
            for w in range(width):
                tile = layer[(h, w)]
                if tile == expected_tile:
                    return True
    return False
