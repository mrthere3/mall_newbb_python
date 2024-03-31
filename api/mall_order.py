# -*- coding=utf-8 -*-
from fastapi import APIRouter, Header, Depends, Query, Path
from api import get_db
from middleware.jwt import MallUserTokenService
from sqlalchemy.orm import Session
from typing import Optional, Union
from common.custom_response import CoustomResponse
from model.model import TbNewbeeMallOrder, TbNewbeeMallUserToken, TbNewbeeMallOrderItem
from enum import Enum
from datetime import datetime
from core import glob_log


class paycode_status(Enum):
    ORDER_PRE_PAY = 0
    ORDER_PAID = 1
    ORDER_PACKAGED = 2
    ORDER_EXPRESS = 3
    ORDER_SUCCESS = 4
    ORDER_CLOSED_BY_MALLUSER = -1
    ORDER_CLOSED_BY_EXPIRED = -2
    ORDER_CLOSED_BY_JUDGE = -3


GetNewBeeMallOrderStatusEnumByStatus = {
    0: "待支付",
    1: "已支付",
    2: "配货完成",
    3: "出库成功",
    4: "交易成功",
    -1: "手动关闭",
    -2: "超时关闭",
    -3: "商家关闭",
    -9: "error",
}


def UserAuth(token: str = Header(...), db: Session = Depends(get_db)):
    # 进行依赖注入 用户权限检查
    return MallUserTokenService.UserJWTAuth(token, db)


order_route = APIRouter(prefix="/api/v1", dependencies=[Depends(UserAuth)])


@order_route.get("/paySuccess")
def paySuccess(
    db: Session = Depends(get_db),
    orderNo: Optional[str] = Query(default=""),
    vailtor_token: Optional[CoustomResponse] = Depends(
        UserAuth
    ),  # 接收父路由依赖的返回值
    payType: Optional[int] = Query(default=""),
):
    if vailtor_token:
        # 权限校验
        return vailtor_token
    error = query_order_success(db, orderNo, payType)
    if not error:
        return CoustomResponse(msg="订单支付成功", status=200)
    else:
        return CoustomResponse(msg=f"订单支付失败,{error}", status=500)


@order_route.put("/order/{orderNo}/finish")
def finishOrder(
    orderNo: str = Path(..., title="订单编号"),
    token: str = Header(..., title="token"),
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),
    db: Session = Depends(get_db),
):
    if vailtor_token:
        return vailtor_token
    error = query_order_finsh(db, orderNo, token)
    if not error:
        glob_log.error("订单签收失败")
        return CoustomResponse(msg="订单签收成功", status=200)
    else:
        return CoustomResponse(msg=f"订单签收失败 {error}", status=500)


@order_route.put("/order/{orderNo}/cancel")
def cancelOrder(
    orderNo: str = Path(..., title="订单编号"),
    token: str = Header(..., title="token"),
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),
    db: Session = Depends(get_db),
):
    if vailtor_token:
        return vailtor_token
    error = query_order_cancel(db, orderNo, token)
    if not error:
        glob_log.error("订单签收失败")
        return CoustomResponse(msg="订单签收成功", status=200)
    else:
        return CoustomResponse(msg=f"订单签收失败 {error}", status=500)


@order_route.get("/order/{orderNo}")
def Detailorder(
    orderNo: str = Path(..., title="订单编号"),
    token: str = Header(..., title="token"),
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),
    db: Session = Depends(get_db),
):
    mallorderdetail = query_order_detail(db, orderNo, token)
    if isinstance(mallorderdetail, dict):
        return CoustomResponse(data=mallorderdetail, status=200)
    else:
        glob_log.error(mallorderdetail)
        return CoustomResponse(msg=f"查询订单详情接口 {mallorderdetail}", status=500)


def query_order_success(
    db: Session, orderNo: Optional[str], payType: Optional[int]
) -> Union[None, Exception]:
    mallOrder: TbNewbeeMallOrder = (
        db.query(TbNewbeeMallOrder)
        .filter(
            TbNewbeeMallOrder.order_no == orderNo, TbNewbeeMallOrder.is_deleted == 0
        )
        .first()
    )
    if mallOrder:
        if mallOrder.order_status != 0:
            return ValueError("订单状态异常")
        try:
            mallOrder.order_status = paycode_status.ORDER_SUCCESS.value
            mallOrder.pay_type = payType
            mallOrder.pay_status = 1
            mallOrder.pay_time = datetime().now()
            mallOrder.update_time = datetime().now()
            db.add(mallOrder)
            # 事务提交
            db.commit()
            return
        except Exception as e:
            glob_log.error(e)
            db.rollback()
            return e
    else:
        return ValueError("没有查询到该订单号")


def query_order_finsh(
    db: Session, orderNo: Optional[str], token: str
) -> Union[None, Exception]:
    usertoken: TbNewbeeMallUserToken = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not usertoken:
        return Exception("不存在的用户")
    mallorder: TbNewbeeMallOrder = (
        db.query(TbNewbeeMallOrder)
        .filter(
            TbNewbeeMallOrder.order_no == orderNo, TbNewbeeMallOrder.is_deleted == 0
        )
        .first()
    )
    if not mallorder:
        return Exception("未查询到记录")
    if usertoken.user_id != mallorder.user_id:
        return Exception("禁止该操作")
    try:
        mallorder.order_status = paycode_status.ORDER_SUCCESS.value
        mallorder.update_time = datetime.now()
        db.add(mallorder)
        db.commit()
        return
    except Exception as e:
        db.rollback()
        return e


def query_order_cancel(db: Session, orderNo: Optional[str], token: str):
    user_token = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not user_token:
        return Exception("不存在的用户")
    mallorder: TbNewbeeMallOrder = (
        db.query(TbNewbeeMallOrder)
        .filter(
            TbNewbeeMallOrder.order_no == orderNo, TbNewbeeMallOrder.is_deleted == 0
        )
        .first()
    )
    if not mallorder:
        return Exception("未查询到记录")
    if user_token.user_id != mallorder.user_id:
        return Exception("禁止该操作")
    if not isinstance(mallorder.order_status, paycode_status):
        return ValueError("订单状态异常")
    try:
        mallorder.order_status = paycode_status.ORDER_CLOSED_BY_MALLUSER.value
        mallorder.update_time = datetime.now()
        db.add(mallorder)
        db.commit()
        return
    except expression as e:
        db.rollback()


def query_order_detail(db: Session, orderNo: Optional[str], token: str):
    user_token = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not user_token:
        return Exception("不存在的用户")
    mallorder: TbNewbeeMallOrder = (
        db.query(TbNewbeeMallOrder)
        .filter(
            TbNewbeeMallOrder.order_no == orderNo, TbNewbeeMallOrder.is_deleted == 0
        )
        .first()
    )
    if not mallorder:
        return Exception("未查询到记录")
    if user_token.user_id != mallorder.user_id:
        return Exception("禁止该操作")
    mallorderitem: TbNewbeeMallOrderItem = (
        db.query(TbNewbeeMallOrderItem)
        .filter(TbNewbeeMallOrderItem.order_id == mallorder.order_id)
        .all()
    )
    if len(mallorderitem) < 1:
        return Exception("订单项不存在")

    newBeeMallorderItemVOS = {
        "goodsId": mallorderitem.goods_id,
        "goodsName": mallorderitem.goods_name,
        "goodsCount": mallorderitem.goods_count,
        "goodsCoverImg": mallorderitem.goods_cover_img,
        "sellingPrice": mallorderitem.selling_price,
    }

    return {
        "orderNo": mallorder.order_no,
        "totalPrice": mallorder.total_price,
        "payStatus": mallorder.pay_status,
        "payType": mallorder.pay_type,
        "payTypeString": GetNewBeeMallOrderStatusEnumByStatus(mallorder.pay_type),
        "payTime": mallorder.pay_time,
        "orderStatus": mallorder.order_status,
        "orderStatusString": GetNewBeeMallOrderStatusEnumByStatus(
            mallorder.order_status
        ),
        "createTime": mallorder.create_time,
        "newBeeMallOderItemVOS": newBeeMallorderItemVOS,
    }
