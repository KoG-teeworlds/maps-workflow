import hashlib
from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleViolation


class Valid(BaseRule):
    def __handle_noop(self, rule, value):
        return

    def __handle_regex(self, rule, value):
        import re
        try:
            regex = re.compile(rule['regex'])
            if regex.match(value):
                return True
            return RuleViolation(message=f"\"{value}\" does not match \"{rule['regex']}\".", errors=[value, "!=", rule['regex']])
        except Exception:
            return RuleViolation(message=f"\"{value}\" does not match \"{rule['regex']}\".", errors=[value, "!=", rule['regex']])

    def __handle_list(self, rule, value):
        values = value.split(",")
        for val in values:
            if val not in rule['values']:
                return RuleViolation(message=f"\"{val}\" in \"{rule['field']}\" is not explicitly set. Allowed values: \"{', '.join(rule['values'])}\".", errors=[val, "in", rule['values']])

    def evaluate(self):
        violations = []
        if hasattr(self.map_file.info, self.params['field']):
            value = getattr(self.map_file.info, self.params['field'])
            value_type = {
                "list": self.__handle_list,
                "regex": self.__handle_regex,
            }
            violations.append(value_type.get(self.params['type'], self.__handle_noop)(self.params, value))

        return violations
    
    def explain(self):
        return ["setting", "in", None]
