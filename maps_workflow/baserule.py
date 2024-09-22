from typing import Dict, List
from pydantic import BaseModel
import twmap


class BaseRule():
    raw_file: str
    map_file: twmap.Map | None
    params: dict

    def __init__(self, raw_file, map_file: twmap.Map | None, params) -> None:
        self.raw_file = raw_file
        self.map_file = map_file

        if params:
            self.params = self.get_params_model()(**params)

    def get_params_model(self):
        raise NotImplemented

    def evaluate(self):
        raise NotImplemented

    def explain(self):
        raise NotImplemented


class BaseRuleConfig(BaseModel):
    name: str
    module: str
    class_name: str
    description: str
    type: str
    depends_on: List[str]
    params: Dict | None
