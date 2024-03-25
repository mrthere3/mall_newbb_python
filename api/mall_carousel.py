from fastapi import Depends
from pydantic import BaseModel
from model.model import (
    TbNewbeeMallCarousel,
    TbNewbeeMallIndexConfig,
    TbNewbeeMallGoodsInfo,
)
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from core import glob_log
from api import get_db  # route,
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from . import route
from common.custom_response import CoustomResponse
from enum import Enum


class Goodsindex(Enum):
    IndexSearchhots = 1
    IndexSearchDownHots = 2
    IndexGoodsHot = 3
    IndexGoodsNew = 4
    IndexGoodsRecommond = 5


class Carousel(BaseModel):
    carouselUrl: str
    redirectUrl: str


@route.get("/index-infos", response_model=List[Carousel])
def GetCarouselsForIndex(
    num: Optional[int] = 5, db: Session = Depends(get_db)
) -> List[Carousel]:
    mallcarouseinfo = query_carousel(db, num)

    # if not mallcarouseinfo:
    #     glob_log.error("轮播图获取失败")
    #     return CoustomResponse(data, status=500, msg="轮播图获取失败")
    # hotgoodes = queryhotgoods()
    hotgoodses = query_hotgoods(db, 4, Goodsindex.IndexGoodsHot.value)
    newgoodses = query_hotgoods(db, 5, Goodsindex.IndexGoodsNew.value)
    recommendgoodses = query_hotgoods(db, 10, Goodsindex.IndexGoodsRecommond.value)
    indexResult = {
        "carousels": mallcarouseinfo,
        "hotGoodses": hotgoodses,
        "newGoodses": newgoodses,
        "recommendGoodses": recommendgoodses,
    }
    return CoustomResponse(data=indexResult, status=200)


def query_carousel(db: Session, num: Optional[int] = 3) -> List[Carousel]:
    carousels = (
        db.query(TbNewbeeMallCarousel)
        .filter(TbNewbeeMallCarousel.is_deleted == "0")
        .order_by(TbNewbeeMallCarousel.carousel_rank.desc())
        .limit(num)
        .all()
    )

    mallcarouseinfo: List[Carousel] = [
        Carousel(
            carouselUrl=Carouselsin.carousel_url,
            redirectUrl=Carouselsin.redirect_url,
        )
        for Carouselsin in carousels
    ]
    return mallcarouseinfo


def query_hotgoods(
    db: Session, num: Optional[int] = 4, config_type: int = 3
) -> List[Optional[TbNewbeeMallGoodsInfo]]:
    hotgoodsinfo: List[TbNewbeeMallIndexConfig] = (
        db.query(TbNewbeeMallIndexConfig)
        .filter(
            TbNewbeeMallIndexConfig.config_type == config_type,
            TbNewbeeMallIndexConfig.is_deleted == 0,
        )
        .order_by(TbNewbeeMallIndexConfig.config_rank.desc())
        .limit(num)
        .all()
    )
    hotgoodsid: List[int] = [hotgood.goods_id for hotgood in hotgoodsinfo]
    goodslist: List[TbNewbeeMallGoodsInfo] = (
        db.query(TbNewbeeMallGoodsInfo)
        .filter(TbNewbeeMallGoodsInfo.goods_id.in_(hotgoodsid))
        .all(),
    )
    goodsinfo_list = list()
    if goodslist:
        for good in goodslist[0]:
            goodsinfo_list.append(
                {
                    "goodId": good.goods_id,
                    "goodsName": (
                        good.goods_name
                        if len(good.goods_name) > 30
                        else good.goods_name[:29] + "..."
                    ),
                    "goodIntro": (
                        good.goods_intro
                        if len(good.goods_intro) > 30
                        else good.goods_intro[:29] + "..."
                    ),
                    "goodsCoverImg": good.goods_cover_img,
                    "sellingPrice": good.selling_price,
                    "tag": good.tag,
                }
            )
        return goodsinfo_list
    else:
        return []
