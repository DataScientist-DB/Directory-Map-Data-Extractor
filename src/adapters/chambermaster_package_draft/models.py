from dataclasses import dataclass


@dataclass
class RawMemberProfile:
    name: str = ""

    phone: str = ""
    fax: str = ""

    email: str = ""
    website: str = ""

    facebook: str = ""
    linkedin: str = ""
    instagram: str = ""
    youtube: str = ""
    twitter: str = ""

    address: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""

    description: str = ""

    hours: str = ""
    driving_directions: str = ""

    category_names: str = ""

    profile_url: str = ""
