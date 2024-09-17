from twmap import Map

from maps_workflow.exceptions import RuleException, RuleViolation


def handle_noop(rule, value):
    return

def handle_regex(rule, value):
    import re
    try:
        regex = re.compile(rule['regex'])
        if regex.match(value):
            return True
        return RuleViolation(message=f"\"{value}\" does not match \"{rule['regex']}\".", errors=[value, "!=", rule['regex']])
    except Exception:
        return RuleViolation(message=f"\"{value}\" does not match \"{rule['regex']}\".", errors=[value, "!=", rule['regex']])

def handle_list(rule, value):
    values = value.split(",")
    for val in values:
        if val not in rule['values']:
            return RuleViolation(message=f"\"{val}\" in \"{rule['field']}\" is not explicitly set. Allowed values: \"{', '.join(rule['values'])}\".", errors=[val, "in", rule['values']])

def is_info_valid(raw_file, tw_map: Map, params: dict):
    violations = []
    if hasattr(tw_map.info, params['field']):
        value = getattr(tw_map.info, params['field'])
        value_type = {
            "list": handle_list,
            "regex": handle_regex,
        }
        violations.append(value_type.get(params['type'], handle_noop)(params, value))

    return violations
