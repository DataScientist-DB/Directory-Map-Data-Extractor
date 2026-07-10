from __future__ import annotations


class DirectorySelector:
    """
    Determines which directory adapters
    should satisfy the user's request.
    """

    def select(self, request: SearchRequest):

        directories = []

        if request.country == "USA":
            directories += [
                "bbb",
                "chambermaster",
                "yelp",
            ]

        if request.country == "Canada":
            ...

        return directories
