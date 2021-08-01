from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ._exceptions import ApiError


def api_error_handler(_: Request, exc: ApiError):
    return JSONResponse({"message": exc.get_message()}, status_code=exc.status_code)


def set_api_error_handler(app: FastAPI):
    app.add_exception_handler(ApiError, api_error_handler)

