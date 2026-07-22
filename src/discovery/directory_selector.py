from __future__ import annotations


class DirectorySelector:

    def select(
        self,
        request,
    ) -> list[str]:

        if request.directories:
            return request.directories

        directories = []

        country = (request.country or "").upper()

        if country == "USA":

            directories.extend([
                "bbb",
                "chambermaster",
                "yelp",
            ])

        elif country == "CANADA":

            directories.extend([
                "chambermaster",
            ])

        return directories
