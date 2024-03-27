## -*- coding=utf-8 -*-
from sqlalchemy.orm import Session
from model.model import TbNewbeeMallUserToken
from typing import Tuple
from common.custom_response import CoustomResponse
from datetime import datetime


class MallUserTokenService:
    @staticmethod
    def ExistUserToken(token: str, db: Session) -> TbNewbeeMallUserToken:
        return (
            db.query(TbNewbeeMallUserToken)
            .filter(TbNewbeeMallUserToken.token == token)
            .first()
        )

    @staticmethod
    def UserJWTAuth(token: str, db: Session):
        if token == "":
            return CoustomResponse(status=416, msg="未登录")
        mallusertoken: TbNewbeeMallUserToken = MallUserTokenService.ExistUserToken(
            token, db
        )
        if datetime.now() > mallusertoken.expire_time:
            MallUserTokenService.DeleteMallUserToken(db, token)
            return CoustomResponse(status=500, msg="授权已过期")
        else:
            return

    @staticmethod
    def DeleteMallUserToken(db: Session, token: str):
        expire_token = (
            db.query(TbNewbeeMallUserToken)
            .filter(TbNewbeeMallUserToken.token == token)
            .first()
        )
        db.delete(expire_token)
