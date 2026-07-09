from __future__ import annotations


class DirectorySelector:
    """
    Determines which directory adapters
    should satisfy the user's request.
    """

    def select(self, request):

        if request.directories:
            return request.directories

        return [
            "bbb",
            "chambermaster",
        ]
