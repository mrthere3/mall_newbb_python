# -*- coding=utf-8 -*-
from fastapi import APIRouter, Header, Depends, Query
from api import get_db
from middleware.jwt import MallUserTokenService
from sqlalchemy.orm import Session
from typing import Optional
from common.custom_response import CoustomResponse
from model.model import TbNewbeeMallOrder
from enum import Enum
from datetime import datetime
from core import glob_log


class paycode_status(Enum):
    ORDER_PRE_PAY: 0
    ORDER_PAID: 1
    ORDER_PACKAGED: 2
    ORDER_EXPRESS: 3
    ORDER_SUCCESS: 4
    ORDER_CLOSED_BY_MALLUSER: -1
    ORDER_CLOSED_BY_EXPIRED: -2
    ORDER_CLOSED_BY_JUDGE: -3


def UserAuth(token: str = Header(default=""), db: Session = Depends(get_db)):
    # 进行依赖注入 用户权限检查
    print("yes")
    return MallUserTokenService.UserJWTAuth(token, db)


order_route = APIRouter(prefix="/api/v1", dependencies=[Depends(UserAuth)])


@order_route.get("/paySuccess")
def paySuccess(
    orderNo: Optional[str] = Query(default=""),
    vailtor_token: Optional[CoustomResponse] = Depends(
        UserAuth
    ),  # 接收父路由依赖的返回值
    payType: Optional[int] = Query(default=""),
):
    if vailtor_token:
        return token
    error = query_order_success(db, orderNo, payType)
    if not isinstance(error, Exception):
        return CoustomResponse(msg="订单支付成功", status=200)
    else:
        return CoustomResponse(msg=f"订单支付失败{error}", status=500)


def query_order_success(
    db: Session, orderNo: Optional[str], payType: Optional[int]
) -> bool:
    mallOrder: TbNewbeeMallOrder = (
        db.query(TbNewbeeMallOrder)
        .filter(
            TbNewbeeMallOrder.order_no == orderNo, TbNewbeeMallOrder.is_deleted == 0
        )
        .first()
    )
    if mallOrder:
        if mallOrder.order_status != 0:
            raise ValueError("订单状态异常")
        try:
            mallOrder.order_status = paycode_status.ORDER_SUCCESS.value
            mallOrder.pay_type = payType
            mallOrder.pay_status = 1
            mallOrder.pay_time = datetime().now()
            mallOrder.update_time = datetime().now()
            db.add(mallOrder)
            return
        except Exception as e:
            glob_log.error(e)
            return e
            db.rollback()
