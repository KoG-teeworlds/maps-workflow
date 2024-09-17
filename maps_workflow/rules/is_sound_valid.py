from twmap import Map
import hashlib

from maps_workflow.exceptions import RuleException


def is_sound_valid(raw_file, tw_map: Map, params):
    violations = []
    for sound in tw_map.sounds:
        print(sound.name)
        data_str = str(sound.data).encode('utf-8')
        sha512_hash = hashlib.sha512()
        sha512_hash.update(data_str)
        print(sha512_hash.hexdigest())

    return violations
