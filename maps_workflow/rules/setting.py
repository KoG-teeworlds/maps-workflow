from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleViolation


class Valid(BaseRule):
    def __handle_noop(self, rule_name, rule, value):
        return

    def __handle_regex(self, rule_name, rule, value):
        print(rule)

    def __handle_list(self, rule_name, rule, value):
        values = value.split(",")
        for val in values:
            if val not in rule['values']:
                return RuleViolation(message=f"{val} is not in {rule['values']}", errors=[])
        return None

    def evaluate(self):
        violations = []

        if hasattr(self.map_file.info.settings, self.params['field']):
            value = getattr(self.map_file.info.settings, self.params['field'])
            value_type = {
                "list": self.__handle_list,
                "regex": self.__handle_regex,
            }
            violations.append(value_type.get(self.params['type'], self.__handle_noop)(self.params, value))

        return violations
    
    def explain(self):
        return ["setting", "in", None]
