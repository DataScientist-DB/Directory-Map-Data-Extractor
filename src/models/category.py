from dataclasses import dataclass


@dataclass
class BusinessCategory:
    name: str
    url: str = ""
    code: str = ""
