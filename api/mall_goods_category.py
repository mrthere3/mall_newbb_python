# -*- coding:utf-8 -*-
from fastapi import Depends, Path
from pydantic import BaseModel
from model.model import TbNewbeeMallGoodsCategory
from common.custom_response import CoustomResponse
from core import glob_log
from api import get_db  # route,
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from . import route
import enum


class CategoryLevel(enum.Enum):
    Default = 0
    LevelOne = 1
    LevelTwo = 2
    LevelThree = 3

    def code(self) -> int:
        return self.value


class ThirdLevelCategoryVO(BaseModel):
    categoryId: Optional[int]
    categoryLevel: Optional[int]
    categoryName: Optional[str]


class SecondLevelCategoryVO(BaseModel):
    categoryId: Optional[int]
    parentId: Optional[int]
    categoryLevel: Optional[int]
    categoryName: Optional[str]
    thirdLevelCategoryVOS: List[Optional[ThirdLevelCategoryVO]] = []


class NewBeeMallIndexCategoryVO(BaseModel):
    categoryId: Optional[int]
    categoryLevel: Optional[int]
    categoryName: Optional[str]
    secondLevelCategoryVOS: List[Optional[SecondLevelCategoryVO]]


@route.get("/categories")
def GetGoodsCategory(db: Session = Depends(get_db)):
    category = GetGoodsCategory(db)
    return CoustomResponse(data=category, msg="SUCCESS", status=200)


def GetGoodsCategory(db: Session):
    newBeeMallIndexCategoryVOS: List[NewBeeMallIndexCategoryVO] = list()
    firstLevelCategories = selectByLevelAndParentIdsAndNumber(
        db, TbNewbeeMallGoodsCategory, [0], CategoryLevel.LevelOne.code(), 10
    )
    if firstLevelCategories:
        firstLevelCategoryIds: List[int] = list()
        for firstLevelCategorie in firstLevelCategories:
            firstLevelCategoryIds.append(firstLevelCategorie.category_id)
        secondLevelCategories = selectByLevelAndParentIdsAndNumber(
            db,
            TbNewbeeMallGoodsCategory,
            firstLevelCategoryIds,
            CategoryLevel.LevelTwo.code(),
            0,
        )
        if secondLevelCategories:
            secondLevelCategoryIds: List[int] = list()
            for secondLevelCategorie in secondLevelCategories:
                secondLevelCategoryIds.append(secondLevelCategorie.category_id)
            thirdLevelCategories = selectByLevelAndParentIdsAndNumber(
                db,
                TbNewbeeMallGoodsCategory,
                secondLevelCategoryIds,
                CategoryLevel.LevelThree.code(),
                0,
            )
            if thirdLevelCategories:
                thirdLevelCategoryMap: Dict[
                    int, List[Optional[TbNewbeeMallGoodsCategory]]
                ] = dict()
                for thirdLevelCategory in thirdLevelCategories:
                    thirdLevelCategoryMap[thirdLevelCategory.parent_id] = []
                for k, v in thirdLevelCategoryMap.items():
                    for third in thirdLevelCategories:
                        if k == third.parent_id:
                            v.append(third)
                        thirdLevelCategoryMap[k] = v
                secondLevelCategoryVOS: List[SecondLevelCategoryVO] = list()
                for secondLevelCategory in secondLevelCategories:
                    secondLevelCategoryVO = SecondLevelCategoryVO(
                        categoryId=secondLevelCategory.category_id,
                        parentId=secondLevelCategory.parent_id,
                        categoryLevel=secondLevelCategory.category_level,
                        categoryName=secondLevelCategory.category_name,
                        thirdLevelCategoryVOS=[],
                    )
                    if thirdLevelCategoryMap.get(secondLevelCategory.category_id, ""):
                        tempGoodsCategories = thirdLevelCategoryMap[
                            secondLevelCategory.category_id
                        ]
                        thirdLevelCategoryRes = [
                            ThirdLevelCategoryVO(
                                categoryId=tempGoodsCategorie.category_id,
                                categoryLevel=tempGoodsCategorie.category_level,
                                categoryName=tempGoodsCategorie.category_name,
                            )
                            for tempGoodsCategorie in tempGoodsCategories
                        ]
                        secondLevelCategoryVO.thirdLevelCategoryVOS.extend(
                            thirdLevelCategoryRes
                        )
                        secondLevelCategoryVOS.append(secondLevelCategoryVO)
                if secondLevelCategoryVOS:
                    secondLevelCategoryVOMap: Dict[
                        int, Optional[SecondLevelCategoryVO]
                    ] = dict()
                    for secondLevelCategory in secondLevelCategoryVOS:
                        secondLevelCategoryVOMap[secondLevelCategory.parentId] = []
                    for k, v in secondLevelCategoryVOMap.items():
                        for second in secondLevelCategoryVOS:
                            if k == second.parentId:
                                v.append(
                                    SecondLevelCategoryVO(
                                        categoryId=second.categoryId,
                                        categoryLevel=second.categoryLevel,
                                        categoryName=second.categoryName,
                                        parentId=second.parentId,
                                        thirdLevelCategoryVOS=second.thirdLevelCategoryVOS,
                                    )
                                )
                            secondLevelCategoryVOMap[k] = v
                    for firstCategory in firstLevelCategories:
                        newBeeMallIndexCategoryVO = NewBeeMallIndexCategoryVO(
                            categoryId=firstCategory.category_id,
                            categoryName=firstCategory.category_name,
                            categoryLevel=firstCategory.category_level,
                            secondLevelCategoryVOS=[],
                        )
                        if secondLevelCategoryVOMap.get(firstCategory.category_id, ""):
                            tempGoodsCategories = secondLevelCategoryVOMap[
                                firstCategory.category_id
                            ]
                            newBeeMallIndexCategoryVO.secondLevelCategoryVOS = (
                                tempGoodsCategories
                            )
                            newBeeMallIndexCategoryVOS.append(newBeeMallIndexCategoryVO)
    return newBeeMallIndexCategoryVOS


def selectByLevelAndParentIdsAndNumber(
    db: Session,
    category: TbNewbeeMallGoodsCategory,
    ids: List[int],
    level: int,
    limit: int,
) -> List[TbNewbeeMallGoodsCategory]:
    result = (
        db.query(category)
        .filter(
            category.parent_id.in_(ids),
            category.category_level == level,
            category.is_deleted == 0,
        )
        .order_by(category.category_rank.desc())
    )

    if limit == 0:
        result = result.all()
    else:
        result = result.limit(limit).all()
    return result
