from pydantic import BaseModel
from twmap import Map
import os

from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleViolation



class FileSizeParams(BaseModel):
    max_file_size: str


class FileSize(BaseRule):
    params: FileSizeParams

    def get_params_model(self):
        return FileSizeParams

    def convert_size_to_bytes(self, size_str: str):
        size_str = size_str.strip().upper()
        units = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
        
        for unit in units:
            if size_str.endswith(unit):
                return float(size_str[:-len(unit)]) * units[unit]
        
        raise ValueError("Unknown size unit. Please use KB, MB, or GB.")

    def evaluate(self):
        violations = []
        allowed_size = self.convert_size_to_bytes(self.params.max_file_size)
        stat = os.stat(self.raw_file)
        if stat.st_size >= allowed_size:
            violations.append(RuleViolation(message=f"The filesize is above the allowed limit of {self.params.max_file_size}.", errors=[stat.st_size, ">", allowed_size]))
        return violations
    
    def explain(self):
        return ["file_size", ">", self.params.max_file_size]
