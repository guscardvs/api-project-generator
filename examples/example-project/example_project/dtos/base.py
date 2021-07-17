import re

from pydantic.main import BaseModel

_to_camel_exp = re.compile("_([a-zA-Z])")


class DTO(BaseModel):
    class Config:
        allow_population_by_field_name = True
        allow_mutation = False
        use_enum_values = True

        @classmethod
        def alias_generator(cls, string):
            return re.sub(_to_camel_exp, lambda match: match[1].upper(), string)
