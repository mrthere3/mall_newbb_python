# -*- coding=utf-8 -*-
from fastapi import APIRouter, Header, Depends, Query, Path
from api import get_db
from middleware.jwt import MallUserTokenService
from sqlalchemy.orm import Session
from typing import Optional, Union, List, Dict
from common.custom_response import CoustomResponse
from model.model import (
    TbNewbeeMallOrder,
    TbNewbeeMallShoppingCartItem,
    TbNewbeeMallUserToken,
    TbNewbeeMallOrderItem,
    TbNewbeeMallShoppingCartItem,
    TbNewbeeMallGoodsInfo,
    TbNewbeeMallUserAddres,
)
from pydantic import BaseModel, validator
from datetime import datetime


class CartItemResponse(BaseModel):
    cartItemId: int
    goodsId: int
    goodsCount: int
    goodsName: str
    goodsCoverImg: str
    sellingPrice: int


class SaveCartItemParam(BaseModel):
    goodsCount: int
    goodsId: int

    @validator("goodsCount")
    def count_must_not_valitor(cls, v):
        if v < 1:
            raise ValueError("商品数量不能小于 1 ！")
        elif v > 5:
            raise ValueError("超出单个商品的最大购买数量！")
        return v


class MallShoppingCartItem(BaseModel):
    cartItemId: int
    userId: int
    goodsId: int
    goodsCount: int
    isDeleted: int
    createTime: datetime
    updateTime: datetime


def UserAuth(token: str = Header(...), db: Session = Depends(get_db)):
    # 进行依赖注入 用户权限检查
    return MallUserTokenService.UserJWTAuth(token, db)


order_route = APIRouter(prefix="/api/v1", dependencies=[Depends(UserAuth)])


@order_route.get("/shop-cart")
def paySuccess(
    db: Session = Depends(get_db),
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),  # 接收父路由依赖的返回值
    token: str = Header(..., title="token"),
):
    if vailtor_token:
        # 权限校验
        return vailtor_token
    CartItems = GetMyShoppingCartItems(db, token)
    if isinstance(CartItems, Exception):
        return CoustomResponse(msg=f"获取购物车失败,{CartItems}", status=500)
    else:
        return CoustomResponse(msg="获取购物车失败", data=CartItems, status=200)


@order_route.post("/shop-cart")
def paySuccess(
    req: SaveCartItemParam,
    db: Session = Depends(get_db),
    vailtor_token: Optional[CoustomResponse] = Depends(UserAuth),  # 接收父路由依赖的返回值
    token: str = Header(..., title="token"),
):
    if vailtor_token:
        # 权限校验
        return vailtor_token
    cartitem = SaveMallCartItem(db, token, req)
    if isinstance(cartitem, Exception):
        return CoustomResponse(msg=f"获取购物车失败,{cartitem}", status=500)
    elif isinstance(cartitem, bool):
        return CoustomResponse(msg="获取购物车失败", data=cartitem, status=200)


def GetMyShoppingCartItems(
    db: Session, token: str
) -> Union[List[CartItemResponse], Exception]:
    usertoken: TbNewbeeMallUserToken = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not usertoken:
        return Exception("不存在的用户")
    cartItems: List[CartItemResponse] = []
    shopCartItems: List[TbNewbeeMallShoppingCartItem] = (
        db.query(TbNewbeeMallShoppingCartItem)
        .filter(
            TbNewbeeMallShoppingCartItem.user_id == usertoken.user_id,
            TbNewbeeMallShoppingCartItem.is_deleted == 0,
        )
        .all()
    )
    goodsIds = [shoppingCartItem.goods_id for shoppingCartItem in shopCartItems]
    goodsInfos: List[TbNewbeeMallGoodsInfo] = (
        db.query(TbNewbeeMallGoodsInfo)
        .filter(TbNewbeeMallGoodsInfo.goods_id.in_(goodsIds))
        .all()
    )
    goodsMap = {}
    for goodsInfo in goodsInfos:
        goodsMap[goodsInfo.goods_id] = goodsInfo
    for v in shopCartItems:
        cartItem = CartItemResponse()
        cartItem.cartItemId = v.cart_item_id
        cartItem.goodsId = v.goods_id
        cartItem.goodsCount = v.goods_count
        if goodsInfo := goodsMap.get(v.goods_id, ""):
            cartItem.goodsName = goodsInfo.goods_name
            cartItem.goodsCoverImg = goodsInfo.goods_cover_img
            cartItem.sellingPrice = goodsInfo.selling_price
        cartItems.append(cartItem)
    return cartItems


def SaveMallCartItem(
    db: Session, token: str, req: SaveCartItemParam
) -> Union[bool, Exception]:
    usertoken: TbNewbeeMallUserToken = (
        db.query(TbNewbeeMallUserToken)
        .filter(TbNewbeeMallUserToken.token == token)
        .first()
    )
    if not usertoken:
        return Exception("不存在的用户")
    good_is_existence: TbNewbeeMallGoodsInfo = (
        db.query(TbNewbeeMallShoppingCartItem)
        .filter(
            TbNewbeeMallShoppingCartItem.goods_id == req.goodsId,
            TbNewbeeMallShoppingCartItem.user_id == usertoken.user_id,
            TbNewbeeMallShoppingCartItem.is_deleted == 0,
        )
        .first()
    )
    if good_is_existence:
        return Exception("已存在,无需重复添加")
    mall_goods_info: TbNewbeeMallGoodsInfo = (
        db.query(TbNewbeeMallGoodsInfo)
        .filter(TbNewbeeMallGoodsInfo.goods_id == req.goodsId)
        .first()
    )
    if not mall_goods_info:
        return Exception("商品为空")
    query = db.query(TbNewbeeMallShoppingCartItem)
    total = query.filter(
        TbNewbeeMallShoppingCartItem.user_id == usertoken.user_id,
        TbNewbeeMallShoppingCartItem.is_deleted == 0,
    ).count()
    if total > 20:
        return Exception("超出购物车最大容量")
    shopCartItem = TbNewbeeMallShoppingCartItem()
    shopCartItem.goods_id = req.goodsId
    shopCartItem.goods_count = req.goodsCount
    shopCartItem.user_id = usertoken.user_id
    shopCartItem.create_time = datetime.now()
    shopCartItem.update_time = datetime.now()
    try:
        db.add(shopCartItem)
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        return e
    return True
