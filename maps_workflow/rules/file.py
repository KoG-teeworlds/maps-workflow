from typing import Optional
from pydantic import BaseModel
import operator
import os

from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleViolation



class FileSizeParams(BaseModel):
    max_file_size: Optional[str] = None
    min_file_size: Optional[str] = None


class FileSize(BaseRule):
    params: FileSizeParams

    def get_params_model(self):
        return FileSizeParams

    def convert_size_to_bytes(self, size_str: str):
        size_str = size_str.strip().upper()
        units = {"BB": 1024, "KB": 1024**2, "MB": 1024**3, "GB": 1024**4}

        for unit in units:
            if size_str.endswith(unit):
                return float(size_str[:-len(unit)]) * units[unit]
        
        raise ValueError("Unknown size unit. Please use B, KB, MB or GB.")

    def evaluate(self):
        violations = []
        file_size = None
        op = None

        if self.params.max_file_size:
            file_size = self.params.max_file_size
            op = operator.gt
        elif self.params.min_file_size:
            file_size = self.params.min_file_size
            op = operator.lt

        allowed_size = self.convert_size_to_bytes(file_size)
        stat = os.stat(self.raw_file)
        if op(stat.st_size, allowed_size):
            violations.append(RuleViolation(message=f"The filesize is above the allowed limit of {self.params.max_file_size}.", errors=[stat.st_size, operator, file_size]))
        return violations
    
    def explain(self):
        return ["file_size", ">", self.params.max_file_size]
