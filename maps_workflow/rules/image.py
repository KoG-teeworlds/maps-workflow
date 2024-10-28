import hashlib

from pydantic import BaseModel
from maps_workflow.baserule import BaseRule
from maps_workflow.exceptions import RuleViolation


class ValidParams(BaseModel):
    pass


class Valid(BaseRule):
    params: ValidParams

    def get_params_model(self):
        return ValidParams

    def evaluate(self):
        violations = []
        for image in self.map_file.images:
            if image.height() % 16 != 0:
                violations.append(RuleViolation(message=f"{image.name} height is not divisable by 16, may encounter visual bugs", errors=[image.height(), "%", 16]))
            
            if image.width() % 16 != 0:
                violations.append(RuleViolation(message=f"{image.name} width is not divisable by 16, may encounter visual bugs", errors=[image.width(), "%", 16]))

            if image.is_embedded():
                if image.data is not None and image.data.size > 0:
                    sha512_hash = hashlib.sha512()
                    sha512_hash.update(image.data.all().tobytes())

                    print(image.name)
                    print(sha512_hash.hexdigest())
                    # TODO: Check hash against known hashes otherwise ask for permission
                else:
                    violations.append(RuleViolation(message=f"{image.name} is embedded but has no data.", errors=[image.data.size, ">", 0]))

            if image.is_external():
                print(f"{image.name} is external, looking it up in mapres")

        return violations
    
    def explain(self):
        return ["setting", "in", None]
