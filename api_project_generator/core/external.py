import urllib.request as _request

from gyver.utils import json

from api_project_generator.core.cache import Cache, CacheMiss


def get(url: str):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/vnd.pypi.simple.v1+json",
    }
    response = _request.urlopen(_request.Request(url, headers=headers, method="GET"))
    return json.loads(response.read().decode())


uri_template = "https://pypi.org/pypi/{package}/json"


def get_package_info(package: str, cache: Cache):
    try:
        return json.loads(cache.get(package))
    except CacheMiss:
        response = get(uri_template.format(package=package))
        cache.set(package, json.dumps(response))
        return response


def get_python_ignore(cache: Cache):
    filename = "Python.gitignore"
    try:
        return cache.get_file(filename).decode()
    except CacheMiss:
        url = (
            "https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore"
        )
        response = _request.urlopen(_request.Request(url, method="GET"))
        contents = response.read()
        cache.set_file(filename, contents)
        return contents.decode()
