import twmap


class BaseRule():
    raw_file: str
    map_file: twmap.Map | None
    params: dict

    def __init__(self, raw_file, map_file: twmap.Map | None, params) -> None:
        self.raw_file = raw_file
        self.map_file = map_file
        self.params = params

    def evaluate(self):
        raise NotImplemented

    def explain(self):
        raise NotImplemented
