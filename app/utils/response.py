from fastapi.responses import JSONResponse


def success_response(data, message, http_status=200):
    respose_dict = {
        "data": data,
        "message": message,
    }
    return JSONResponse(status_code=http_status, content=respose_dict)


def error_response(message, code=None, http_status=500):
    respose_dict = {"error": {"code": code, "message": message}}
    return JSONResponse(status_code=http_status, content=respose_dict)