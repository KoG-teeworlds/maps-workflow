from typing import List, Optional

from pydantic import BaseModel
from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleViolation


class ValidParams(BaseModel):
    field: str
    type: str
    regex: Optional[str] = None
    values: Optional[List[str]] = []


class Valid(BaseRule):
    params: ValidParams

    def get_params_model(self):
        return ValidParams

    def __handle_noop(self, value: str):
        return RuleViolation(message=f"Type not implemented!", errors=[])

    def __handle_regex(self, value: str):
        import re
        try:
            regex: re.Pattern = re.compile(self.params.regex)
            if regex.match(value):
                return True
            return RuleViolation(message=f"\"{value}\" does not match \"{self.params.regex}\".", errors=[value, "!=", self.params.regex])
        except Exception:
            return RuleViolation(message=f"\"{value}\" does not match \"{self.params.regex}\".", errors=[value, "!=", self.params.regex])

    def __handle_list(self, value: str):
        values = value.split(",")
        for val in values:
            if val not in self.params.values:
                return RuleViolation(message=f"\"{val}\" in \"{self.params.field}\" is not explicitly set. Allowed values: \"{', '.join(self.params.values)}\".", errors=[val, "in", self.params.values])

    def evaluate(self):
        violations = []
        if hasattr(self.map_file.info, self.params.field):
            value = getattr(self.map_file.info, self.params.field)
            value_type = {
                "list": self.__handle_list,
                "regex": self.__handle_regex,
            }
            
            violations.append(value_type.get(self.params.type, self.__handle_noop)(value))
        return violations

    def explain(self):
        return ["setting", "in", None]
