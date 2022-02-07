from enum import Enum
from dataclasses import dataclass

import requests

from .models import *


class IndexType(Enum):
    """Type to sort search results by"""

    RELEVANCE = "relevance"
    DOWNLOADS = "downloads"
    FOLLOWS = "follows"
    NEWEST = "newest"
    UPDATED = "updated"


@dataclass
class SearchResults:
    """Search results from a search query"""

    results: list[SearchResultModel]
    offset: int
    limit: int
    total_hits: int


class Session:
    API_BASE_URL = 'https://api.modrinth.com/v2/'

    def __init__(self, github_token: str = None):
        self.github_token = github_token

    def request(self, method: str, sub_url: str, **kwargs) -> requests.Response:
        if self.github_token:
            kwargs['headers'] = {
                'Authorization': self.github_token
            }
        res = requests.request(method, self.API_BASE_URL + sub_url, **kwargs)
        # TODO: Handle errors
        res.raise_for_status()
        return res

    def get(self, sub_url: str, **kwargs) -> requests.Response:
        return self.request('GET', sub_url, **kwargs)

    def post(self, sub_url: str, **kwargs) -> requests.Response:
        return self.request('POST', sub_url, **kwargs)

    def put(self, sub_url: str, **kwargs) -> requests.Response:
        return self.request('PUT', sub_url, **kwargs)

    def delete(self, sub_url: str, **kwargs) -> requests.Response:
        return self.request('DELETE', sub_url, **kwargs)

    def patch(self, sub_url: str, **kwargs) -> requests.Response:
        return self.request('PATCH', sub_url, **kwargs)

    def search_projects(
            self,
            *,
            query: str = None,
            facets: list[list[str]] = None,
            index_type: IndexType = None,
            offset: int = None,
            limit: int = None,
            filters: str = None,
    ):
        params = {}
        if query:
            params["query"] = query

        if facets:
            params["facets"] = facets

        if index_type:
            params["index_type"] = index_type.value

        if offset:
            params["offset"] = offset

        if limit:
            params["limit"] = limit

        if filters:
            params["filters"] = filters

        res = self.get("search", params=params)

        results = []

        as_json = res.json()

        for hit in as_json["hits"]:
            results.append(SearchResultModel.from_data(hit))

        return SearchResults(results, as_json["offset"], as_json["limit"], as_json["total_hits"])
