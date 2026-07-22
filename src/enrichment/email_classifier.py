from __future__ import annotations


class EmailClassifier:
    ROLE_MAP = {
        "info": "general",
        "contact": "general",
        "office": "general",
        "admin": "admin",
        "sales": "sales",
        "marketing": "marketing",
        "support": "support",
        "help": "support",
        "hr": "hr",
        "careers": "recruitment",
        "jobs": "recruitment",
        "billing": "finance",
        "accounts": "finance",
        "accounting": "finance",
        "owner": "executive",
        "ceo": "executive",
        "president": "executive",
    }

    FREE_PROVIDERS = {
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "aol.com",
        "icloud.com",
    }

    def classify(self, email: str) -> str:
        local = email.split("@", 1)[0].lower()
        domain = email.split("@", 1)[1].lower()

        if domain in self.FREE_PROVIDERS:
            return "free_provider"

        clean_local = local.replace(".", "").replace("_", "").replace("-", "")

        if local in self.ROLE_MAP:
            return self.ROLE_MAP[local]

        if clean_local in self.ROLE_MAP:
            return self.ROLE_MAP[clean_local]

        if "." in local or "_" in local or "-" in local:
            return "personal"

        return "unknown"
