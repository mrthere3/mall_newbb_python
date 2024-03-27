from fastapi.responses import JSONResponse
from bson.json_util import dumps
from fastapi.encoders import jsonable_encoder


class CoustomResponse(JSONResponse):
    def __init__(
        self, data="", msg="", status=200, media_type="application/json;charset=utf-8"
    ):
        res = dict()
        # 兼容自定义类的json序列化  或者重写to_dict方法
        res["resultCode"] = status
        res["data"] = jsonable_encoder(data)
        res["message"] = msg

        super().__init__(content=res, media_type=media_type, status_code=status)
