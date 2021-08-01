import json
import urllib.request as _request


def get(url: str):
    headers = {"Content-Type":"application/json; charset=utf-8", "Accept":"application/json"}
    response = _request.urlopen(_request.Request(url, headers=headers, method="GET"))
    return json.load(response)