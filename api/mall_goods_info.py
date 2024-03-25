# -*- coding:utf-8 -*-
from fastapi import Depends, Path
from pydantic import BaseModel
from model.model import TbNewbeeMallGoodsInfo
from common.custom_response import CoustomResponse
from core import glob_log
from api import get_db  # route,
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Union
from . import route


class GoodsSearchReasponse(BaseModel):
    GoodsId: int
    Goodsname: str
    GoodsIntro: str
    GoodsCoverImg: str
    SellingPrice: int


class GoodsInfoDetailResponse(BaseModel):
    goodsId: Optional[int] = 0
    goodsName: Optional[str]
    goodsIntro: Optional[str]
    goodsCoverImg: Optional[str]
    sellingPrice: Optional[str]
    goodsDetailContent: Optional[str] = 0
    originalPrice: Optional[int] = 0
    tag: Optional[str]
    goodsCarouselList: List[Optional[str]]


@route.get("/search")
def GoodsSearch(
    pageNumber: Optional[str] = 1,
    goodsCategoryId: Optional[int] = None,
    keyword: Optional[str] = None,
    orderBy: Optional[str] = None,
    db: Session = Depends(get_db),
):
    goodsinfo, total = MallGoodsByCategory(
        db,
        pageNumber,
        goodsCategoryId,
        keyword,
        orderBy,
    )
    glob_log.info(total)
    content = {
        "list": goodsinfo,
        "totalcount": total,
        "currPage": pageNumber,
        "pageSize": 10,
        "totalPage": 0,
    }
    return CoustomResponse(data=content, status=200, msg="获取成功")


@route.get("/goods/detail/{id}")
def GoodsDetail(id: Optional[int] = Path(title="商品编号"), db: Session = Depends(get_db)):
    goodsInfo: TbNewbeeMallGoodsInfo = (
        db.query(TbNewbeeMallGoodsInfo)
        .filter(TbNewbeeMallGoodsInfo.goods_id == id)
        .first()
    )
    res = dict()
    if goodsInfo:
        if goodsInfo.goods_sell_status != 0:
            glob_log.error(f"商品{id}已经下架")
            msg = "商品已经下架"
        else:
            res = GoodsInfoDetailResponse(
                goodsCarouselList=[goodsInfo.goods_carousel],
                goodsName=goodsInfo.goods_name,
                goodsId=goodsInfo.goods_id,
                goodsIntro=goodsInfo.goods_intro,
                goodsCoverImg=goodsInfo.goods_cover_img,
                goodsDetailContent=goodsInfo.goods_detail_content,
                sellingPrice=goodsInfo.selling_price,
                originalPrice=goodsInfo.original_price,
                tag=goodsInfo.tag,
            )
            msg = "SUCCESS"
    else:
        return CoustomResponse(data=res, msg="没有查询到相关产品", status=500)
    return CoustomResponse(data=res, msg=msg, status=200)


def MallGoodsByCategory(
    db: Session, pageNumber: int, goodsCategoryId: int, keyword: str, orderBy: str
) -> (List[GoodsSearchReasponse], int):
    db = db.query(TbNewbeeMallGoodsInfo)
    if keyword:
        db = db.filter(
            TbNewbeeMallGoodsInfo.goods_name.like(f"%{keyword}%"),
            TbNewbeeMallGoodsInfo.goods_intro.like(f"%{keyword}%"),
        )
    if goodsCategoryId >= 0:
        db = db.filter(TbNewbeeMallGoodsInfo.goods_category_id == goodsCategoryId)
    count = db.count()
    if orderBy == "new":
        db = db.order_by(TbNewbeeMallGoodsInfo.goods_id.desc())
    elif orderBy == "price":
        db = db.order_by(TbNewbeeMallGoodsInfo.selling_price.asc())
    else:
        db = db.order_by(TbNewbeeMallGoodsInfo.stock_num.desc())
    goods: List[TbNewbeeMallGoodsInfo] = db.limit(10).offset(int(pageNumber) - 1).all()
    Goods_info: List[GoodsSearchReasponse] = [
        GoodsSearchReasponse(
            GoodsId=good.goods_id,
            Goodsname=good.goods_name,
            GoodsIntro=good.goods_intro,
            GoodsCoverImg=good.goods_cover_img,
            SellingPrice=good.selling_price,
        )
        for good in goods
    ]
    return Goods_info, count
