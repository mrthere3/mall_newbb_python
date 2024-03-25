# -*- coding=utf-8 -*-
from fastapi import APIRouter, Header, Depends, Query
from api import get_db
from middleware.jwt import MallUserTokenService
from sqlalchemy.orm import Session

order_route = APIRouter(prefix="/api/v1", dependencies=[Depends(UserAuth)])


def UserAuth(token: str = Header(), db: Session = Depends(get_db)):
    # 进行依赖注入 用户权限检查
    MallUserTokenService.UserJWTAuth(token, db)


@order_route.get("/paySuccess")
def paySuccess(orderNo: Optional[str] = Query()):
    pass
