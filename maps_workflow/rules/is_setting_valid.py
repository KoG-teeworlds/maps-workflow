from twmap import Map

from maps_workflow.exceptions import RuleViolation


def handle_noop(rule_name, rule, value):
    return

def handle_regex(rule_name, rule, value):
    print(rule)

def handle_list(rule_name, rule, value):
    values = value.split(",")
    for val in values:
        if val not in rule['values']:
            return RuleViolation(message=f"{val} is not in {rule['values']}", errors=[])
    return None

def is_setting_valid(raw_file, tw_map: Map, params):
    violations = []

    if hasattr(tw_map.info.settings, params['field']):
        value = getattr(tw_map.info.settings, params['field'])
        value_type = {
            "list": handle_list,
            "regex": handle_regex,
        }
        violations.append(value_type.get(params['type'], handle_noop)(params, value))

    return violations
