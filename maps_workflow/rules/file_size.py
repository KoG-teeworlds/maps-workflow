from twmap import Map
import os

from maps_workflow.exceptions import RuleViolation


def convert_size_to_bytes(size_str):
    size_str = size_str.strip().upper()
    units = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
    
    for unit in units:
        if size_str.endswith(unit):
            return float(size_str[:-len(unit)]) * units[unit]
    
    raise ValueError("Unknown size unit. Please use KB, MB, or GB.")

def file_size(raw_file, tw_map: Map, params):
    violations = []
    allowed_size = convert_size_to_bytes(params['max_file_size'])
    stat = os.stat(raw_file)
    if stat.st_size >= allowed_size:
        violations.append(RuleViolation(message=f"The filesize is above the allowed limit of {params['max_file_size']}.", errors=[stat.st_size, ">", allowed_size]))
    return violations
