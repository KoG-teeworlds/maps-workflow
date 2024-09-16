from twmap import Map


def is_setting_valid(tw_map: Map, params):
    settings: dict = params['allowed']
    for setting in tw_map.info.settings:
        key, value = setting.split(" ")
        rule = settings.get(key)
        if not rule:
            print(f"\tSkipping {key}, because no rule is defined")
            continue
        print(value)
        print(rule)
    return False
