from typing import cast

from git.config import GitConfigParser
from gyver.attrs import define, info


@define
class GitData:
    reader: GitConfigParser = info(default_factory=GitConfigParser)

    def default_fullname(self) -> str:
        return cast(str, self.reader.get_value("user", "name", ""))

    def default_email(self) -> str:
        return cast(str, self.reader.get_value("user", "email", ""))


def get_user_signature(fullname: str, email: str):
    return "{name} <{email}>".format(name=fullname, email=email)
