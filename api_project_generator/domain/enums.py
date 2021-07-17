from typing import Optional
from api_project_generator.functions import clean_name, to_camel, to_snake
from pathlib import Path
from api_project_generator.services import strings


def write_enum_file(enum_file: Path, enum_name: str, auto_opts: Optional[list[str]]):
    with enum_file.open("w") as stream:
        stream.write(
            strings.ENUM_TEMPLATE.format(
                enum_name=to_camel(to_snake(clean_name(enum_name))),
                auto_opts="\n    ".join(
                    strings.ENUM_AUTO_OPTS_TEMPLATE.format(opt=opt, idx=idx)
                    for idx, opt in enumerate(auto_opts or [])
                ),
            )
        )