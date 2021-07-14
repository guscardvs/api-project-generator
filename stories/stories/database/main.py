from stories.core.settings import BASE_DIR
from ._model_finder import ModelFinder
from .metadata import metadata


def preload():
    model_finder = ModelFinder(BASE_DIR /"database" / "tables", BASE_DIR)
    model_finder.find()

def get_metadata():
    preload()
    return metadata
