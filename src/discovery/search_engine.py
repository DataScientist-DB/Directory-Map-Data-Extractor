from __future__ import annotations

from src.discovery.directory_selector import DirectorySelector


class SearchEngine:
    """
    Executes a SearchRequest.

    The user requests companies.

    SearchEngine decides which directories
    should be scanned.
    """

    def __init__(self):
        self.selector = DirectorySelector()

    def select_adapters(self, request):
        return self.selector.select(request)
