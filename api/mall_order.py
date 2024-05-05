# -*- coding=utf-8 -*-
from fastapi import APIRouter, Header, Depends, Query, Path
from sqlalchemy import desc

from api import get_db
from middleware.jwt import MallUserTokenService
from sqlalchemy.orm import Session
from typing import Optional, Union, List, Dict
from common.custom_response import CoustomResponse
from model.model import (
    TbNewbeeMallOrder,
    TbNewbeeMallUserToken,
    TbNewbeeMallOrderItem,
    TbNewbeeMallShoppingCartItem,
    TbNewbeeMallGoodsInfo,
    TbNewbeeMallUserAddres,
)
from enum import Enum
from datetime import datetime
from core import glob_log
from pydantic import BaseModel, validator
import random
import time


class SaverOrderParam(BaseModel):
    cartItemIds: List[int]
    addressId: int

    @validator("cartItemIds")
    def name_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("cartItemIds cannot be empty")
        return v

    @validator("addressId")
    def name_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("addressId cannot be empty")
        return v


# class MallOrder(BaseModel):
#     orderId: int
#     orderNo: str
#     userId: int
#     totalPrice: int
#     payStatus: int
#     payType: int
#     payTime: datetime
#     orderStatus: int
#     extraInfo: str
#     isDeleted: int
#     createTime: datetime
#     updateTime: datetime
#


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
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),  # 接收父路由依赖的返回值
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
    if vailtor_token:
        return vailtor_token
    mallorderdetail = query_order_detail(db, orderNo, token)
    if isinstance(mallorderdetail, dict):
        return CoustomResponse(data=mallorderdetail, status=200)
    else:
        glob_log.error(mallorderdetail)
        return CoustomResponse(msg=f"查询订单详情接口 {mallorderdetail}", status=500)


@order_route.get("/order")
def OrderList(
    pageNumber: int = Query(..., title="订单页数"),
    token: str = Header(..., title="token"),
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),
    db: Session = Depends(get_db),
    status: str = Query(..., title="订单状态"),
):
    if vailtor_token:
        return vailtor_token
    if pageNumber <= 0:
        pageNumber = 1
    error, list_order, total = MallOrderListBySearch(db, token, pageNumber, status)
    if not error:
        return CoustomResponse(
            data={
                "list": list_order,
                "totalCount": total,
                "currPage": pageNumber,
                "pageSize": 5,
            },
            status=200,
        )
    else:
        return CoustomResponse(msg=f"查询订单详情接口 {error}", status=500)


@order_route.post("/saveOrder")
def SaveOrder(
    saverOrderParam: SaverOrderParam,
    token: str = Header(..., title="token"),
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),
    db: Session = Depends(get_db),
):
    if vailtor_token:
        return vailtor_token
    itemsForSave, priceTotal = GetCartItemsForSettle(
        db, token, saverOrderParam.cartItemIds
    )
    if len(itemsForSave) < 1:
        return CoustomResponse(msg="无数据", status=500)
    else:
        if priceTotal < 1:
            return CoustomResponse(msg="价格异常", status=500)
        userAddress = GetMallUserDefaultAddress(db, token)
        if isinstance(userAddress, Exception):
            return CoustomResponse(msg=f"{ userAddress }", status=500)
        else:
            error, orderno = SaveOrdering(db, token, userAddress, itemsForSave)
            if error:
                glob_log.error(f"订单生成失败{ error }")
                return CoustomResponse(msg=f"{error}", status=500)
            else:
                return CoustomResponse(msg="SUCCESS", status=200)


def MallOrderListBySearch(
    db: Session,
    token: str,
    pageNumber: int,
    status: str,
):
    list_order = list()
    total = 0
    query = db.query(TbNewbeeMallOrder)
    usertoken: TbNewbeeMallUserToken = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not usertoken:
        return Exception("不存在的用户"), list_order, total
    if status != "":
        query1 = query.filter(TbNewbeeMallOrder.order_status == status)
    query1 = query.filter(
        TbNewbeeMallOrder.user_id == usertoken.user_id,
        TbNewbeeMallOrder.is_deleted == 0,
    )
    total = query.count()
    offset = 5 * (pageNumber - 1)
    newBeeMallOrders: List[TbNewbeeMallOrder] = (
        query.order_by(desc(TbNewbeeMallOrder.order_id)).offset(offset).all()
    )
    orderListVOS = list()
    orderIds: List[int] = list()
    if total > 0:
        for newBeeMallOrder in newBeeMallOrders:
            mallorder_response = {
                "orderId": newBeeMallOrder.order_id,
                "orderNo": newBeeMallOrder.order_no,
                "totalPrice": newBeeMallOrder.total_price,
                "payType": newBeeMallOrder.pay_type,
                "orderStatus": newBeeMallOrder.order_status,
                "orderStatusString": GetNewBeeMallOrderStatusEnumByStatus[
                    newBeeMallOrder.order_status
                ],
                "createTime": newBeeMallOrder.create_time,
                "newBeeMallOrderItemVOS": [],
            }
            orderIds.append(newBeeMallOrder.order_id)
            # 再for循环里面做多次查询 还是一次查询 之后再做处理?
            orderListVOS.append(mallorder_response)
        orderItems: List[TbNewbeeMallOrderItem] = (
            db.query(TbNewbeeMallOrderItem)
            .filter(TbNewbeeMallOrder.order_id.in_(orderIds))
            .all()
        )
        # 获取所有的商品子类
        itemByOrderIdMap = dict()
        for orderItem in orderItems:
            itemByOrderIdMap[orderItem.order_id] = []
        for k, v in itemByOrderIdMap:
            for orderItem in orderItems:
                if k == orderItem.order_id:
                    # 是否要封装成单独的response类呢?
                    v.append(
                        {
                            # "orderItemId": orderItem.order_item_id,
                            # "orderId": orderItem.order_id,
                            "goodsId": orderItem.goods_id,
                            "goodsName": orderItem.goods_name,
                            "goodsCoverImg": orderItem.goods_cover_img,
                            "sellingPrice": orderItem.selling_price,
                            "goodsCount": orderItem.goods_count,
                            # "createTime": orderItem.create_time,
                        }
                    )
        for newBeeMallOrderListV0 in orderListVOS:
            if orderItemListTemp := itemByOrderIdMap.get(
                newBeeMallOrderListV0["orderId"], ""
            ):
                newBeeMallOrderListV0.newBeeMallOderItemVOS = orderItemListTemp
                list_order = newBeeMallOrderListV0
    return None, list_order, total


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
            mallOrder.pay_time = datetime.now()
            mallOrder.update_time = datetime.now()
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
    except Exception as e:
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
        .first()
    )
    if not mallorderitem:
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
        "payTypeString": GetNewBeeMallOrderStatusEnumByStatus[mallorder.pay_type],
        "payTime": mallorder.pay_time,
        "orderStatus": mallorder.order_status,
        "orderStatusString": GetNewBeeMallOrderStatusEnumByStatus[
            mallorder.order_status
        ],
        "createTime": mallorder.create_time,
        "newBeeMallOderItemVOS": newBeeMallorderItemVOS,
    }


def GetCartItemsForSettle(db: Session, token: str, CartItemIds: List[int]):
    cartItemRes = list()
    user_token = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not user_token:
        return Exception("不存在的用户"), cartItemRes
    shopCartItems: List[TbNewbeeMallShoppingCartItem] = (
        db.query(TbNewbeeMallShoppingCartItem)
        .filter(
            TbNewbeeMallShoppingCartItem.cart_item_id.in_(CartItemIds),
            TbNewbeeMallShoppingCartItem.user_id == user_token.user_id,
        )
        .all()
    )
    cartItemRes = getMallShoppingCartItemVOS(db, shopCartItems)
    priceTotal = 0
    for cartItem in cartItemRes:
        priceTotal += cartItem.get("goodsCount") * cartItem.get("sellingPrice")
    return cartItemRes, priceTotal


def getMallShoppingCartItemVOS(
    db: Session, CartItems: List[TbNewbeeMallShoppingCartItem]
):
    cartItemsRes = list()
    goodIds: List[int] = [cartItem.goods_id for cartItem in CartItems]
    # 查询出所有的goods_id
    newBeeMallGoods: List[TbNewbeeMallGoodsInfo] = (
        db.query(TbNewbeeMallGoodsInfo)
        .filter(TbNewbeeMallGoodsInfo.goods_id.in_(goodIds))
        .all()
    )
    newBeeMallGoodsMap = dict()
    for goodsInfo in newBeeMallGoods:
        newBeeMallGoodsMap[goodsInfo.goods_id] = goodsInfo
    for cartItem in CartItems:
        cartItemRes = {
            "cartItemId": cartItem.cart_item_id,
            "goodsCount": cartItem.goods_count,
            "goodsId": cartItem.goods_id,
        }
        if newBeeMallGoodsTemp := newBeeMallGoodsMap[cartItem.goods_id]:
            cartItemRes["goodsCoverImg"] = newBeeMallGoodsTemp.goods_cover_img
            cartItemRes["goodsName"] = (
                newBeeMallGoodsTemp.goods_name
                if len(newBeeMallGoodsTemp.goods_name) < 28
                else newBeeMallGoodsTemp.goods_name[:27] + "..."
            )
            cartItemRes["sellingPrice"] = newBeeMallGoodsTemp.selling_price
            cartItemsRes.append(cartItemRes)
    return cartItemsRes


def GetMallUserDefaultAddress(db: Session, token: str):
    user_token = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not user_token:
        return Exception("不存在的用户")
    userAddress: TbNewbeeMallUserAddres = (
        db.query(TbNewbeeMallUserAddres)
        .filter(
            TbNewbeeMallUserAddres.user_id == user_token.user_id,
            TbNewbeeMallUserAddres.default_flag == 1,
            TbNewbeeMallUserAddres.is_deleted == 0,
        )
        .first()
    )
    if not userAddress:
        return Exception("不存在默认地址")
    return userAddress


def SaveOrdering(
    db: Session, token: str, userAddress: TbNewbeeMallUserAddres, myShoppingCartItems
):
    orderNo = str()
    user_token: TbNewbeeMallUserToken = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not user_token:
        return Exception("不存在的用户"), orderNo
    itemIdList = [catItem.get("cartItemId") for catItem in myShoppingCartItems]
    goodsIds = [cartItem.get("goodsId") for cartItem in myShoppingCartItems]
    newBeeMallGoods: List[TbNewbeeMallGoodsInfo] = db.query(
        TbNewbeeMallGoodsInfo
    ).filter(TbNewbeeMallGoodsInfo.goods_id.in_(goodsIds).all())
    for mallgoods in newBeeMallGoods:
        if mallgoods.goods_sell_status != 0:
            return Exception("商品已经下架,无法生成订单"), orderNo
    newBeeMallGoodsMap: Dict[int, TbNewbeeMallGoodsInfo] = dict()
    for mallgoods in newBeeMallGoods:
        newBeeMallGoodsMap[mallgoods.goods_id] = mallgoods
    for shoppingCartItemV0 in myShoppingCartItems:
        if not newBeeMallGoodsMap[shoppingCartItemV0.get("goodsId")]:
            return Exception("购物车数据异常"), orderNo
        if (
            shoppingCartItemV0.get("goodsCount")
            > newBeeMallGoodsMap[shoppingCartItemV0.get("goodsId")].stock_num
        ):
            return Exception("库存不足!"), orderNo
    if len(itemIdList) > 0 and len(goodsIds) > 0:
        db.query(TbNewbeeMallShoppingCartItem).filter(
            TbNewbeeMallShoppingCartItem.cart_item_id.in_(itemIdList)
        ).update({TbNewbeeMallShoppingCartItem.is_deleted: 1})
        db.flush()
        db.commit()
        for shoppingCartItemV0 in myShoppingCartItems:
            goodsInfo: TbNewbeeMallGoodsInfo = (
                db.query(TbNewbeeMallGoodsInfo)
                .filter(
                    TbNewbeeMallGoodsInfo.goods_id == shoppingCartItemV0.get("goodsId")
                )
                .fitst()
            )
            try:
                db.query(TbNewbeeMallGoodsInfo).filter(
                    TbNewbeeMallGoodsInfo.goods_id == shoppingCartItemV0.get("goodsId"),
                    TbNewbeeMallGoodsInfo.goodsCount
                    >= shoppingCartItemV0.get("goodsCount"),
                    TbNewbeeMallGoodsInfo.goods_sell_status == 0,
                ).update(
                    {
                        TbNewbeeMallGoodsInfo.stock_num: (
                            goodsInfo.stock_num - shoppingCartItemV0.get("goodsCount")
                        )
                    }
                )
            except Exception as e:
                # 可能更新出错进行事务回滚
                db.rollback()
                return Exception("库存不足"), orderNo
        orderNo = gen_order_no()
        priceTotal = 0
        newBeeMallOrder: TbNewbeeMallOrder = TbNewbeeMallOrder()
        newBeeMallOrder.order_no = orderNo
        newBeeMallOrder.user_id = user_token.user_id
        for newBeeMallShoppingCartItemVO in myShoppingCartItems:
            priceTotal += newBeeMallShoppingCartItemVO.get(
                "goodsCount"
            ) * newBeeMallShoppingCartItemVO.get("sellingPrice")
        if priceTotal < 1:
            return Exception("订单价格异常"), orderNo
        newBeeMallOrder.create_time = datetime.now()
        newBeeMallOrder.update_time = datetime.now()
        newBeeMallOrder.total_price = priceTotal
        newBeeMallOrder.extra_info = ""
        try:
            db.add(newBeeMallOrder)
            db.commit()
        except Exception as e:
            db.rollback()
            return Exception(e), orderNo
        # 生成所有的订单项快照，并保存至数据库
        newBeeMallOrderItems: List[TbNewbeeMallOrderItem] = list()
        for newBeeMallShoppingCartItemVO in myShoppingCartItems:
            newBeeMallOrderItem = TbNewbeeMallOrderItem()
            newBeeMallOrderItem.order_id = newBeeMallOrder.order_id
            newBeeMallOrderItem.create_time = newBeeMallOrder.create_time
            newBeeMallOrderItem.order_item_id = newBeeMallShoppingCartItemVO.get(
                "cartItemId"
            )
            newBeeMallOrderItem.goods_id = newBeeMallShoppingCartItemVO.get("goodsId")
            newBeeMallOrderItem.goods_name = newBeeMallShoppingCartItemVO.get(
                "goodsName"
            )
            newBeeMallOrderItem.goods_cover_img = newBeeMallShoppingCartItemVO.get(
                "goodsCoverImg"
            )
            newBeeMallOrderItem.selling_price = newBeeMallShoppingCartItemVO.get(
                "sellingPrice"
            )
            newBeeMallOrderItem.goods_count = newBeeMallShoppingCartItemVO.get(
                "goodsCount"
            )
            newBeeMallOrderItems.append(newBeeMallOrderItem)
        try:
            db.add_all(newBeeMallOrderItems)
            db.commit()
        except Exception as e:
            db.rollback()
            return Exception(e), orderNo
        return None, orderNo


def gen_order_no():
    numeric = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    r = len(numeric)
    random.seed(time.time_ns())

    sb = ""
    for i in range(4):
        sb += str(random.choice(numeric))

    timestamp = str(int(time.time() * 1000))  # 将当前时间转换为毫秒级时间戳
    return timestamp + sb
