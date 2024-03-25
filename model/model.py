# coding: utf-8
import logging


from loguru import logger
from sqlalchemy import Column, DateTime, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT
from sqlalchemy.ext.declarative import declarative_base


# class InterceptHandler(logging.Handler):
#     def emit(self, record):
#         # Get corresponding Loguru level if it exists
#         try:
#             level = logger.level(record.levelname).name
#         except ValueError:
#             level = record.levelno
#
#         # Find caller from where originated the logged message
#         frame, depth = logging.currentframe(), 2
#         while frame.f_code.co_filename == logging.__file__:
#             frame = frame.f_back
#             depth += 1
#         logger.opt(depth=depth, exception=record.exc_info).log(
#             level, record.getMessage()
#         )
#
#
# logging.basicConfig(handlers=[InterceptHandler()], level=0)
# logging.getLogger("sqlalchemy").setLevel("DEBUG")
Base = declarative_base()
# metadata = Base.metadata


class TbNewbeeMallAdminUser(Base):
    __tablename__ = "tb_newbee_mall_admin_user"

    admin_user_id = Column(BIGINT(20), primary_key=True, comment="管 理员id")
    login_user_name = Column(String(50), nullable=False, comment="管 理员登陆名称")
    login_password = Column(String(50), nullable=False, comment="管理员登陆密码")
    nick_name = Column(String(50), nullable=False, comment="管理员显 示昵称")
    locked = Column(
        TINYINT(4),
        server_default=text("'0'"),
        comment="是否锁定 0未锁定 1已锁定无法登陆",
    )


class TbNewbeeMallAdminUserToken(Base):
    __tablename__ = "tb_newbee_mall_admin_user_token"

    admin_user_id = Column(BIGINT(20), primary_key=True, comment="用 户主键id")
    token = Column(String(32), nullable=False, unique=True, comment="token值(32位字符串)")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="修改时间",
    )
    expire_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="token过期时间",
    )


class TbNewbeeMallCarousel(Base):
    __tablename__ = "tb_newbee_mall_carousel"

    carousel_id = Column(INTEGER(11), primary_key=True, comment="首页轮播图主键id")
    carousel_url = Column(
        String(100), nullable=False, server_default=text("''"), comment="轮播图"
    )
    redirect_url = Column(
        String(100),
        nullable=False,
        server_default=text("'''##'''"),
        comment="点击后的跳转地址(默认不跳转)",
    )
    carousel_rank = Column(
        INTEGER(11),
        nullable=False,
        server_default=text("'0'"),
        comment="排序值(字段越大越靠前)",
    )
    is_deleted = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="删除标识字段(0-未删除 1-已删除)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    create_user = Column(
        INTEGER(11), nullable=False, server_default=text("'0'"), comment="创建者id"
    )
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="修改时间",
    )
    update_user = Column(
        INTEGER(11), nullable=False, server_default=text("'0'"), comment="修改者id"
    )


class TbNewbeeMallGoodsCategory(Base):
    __tablename__ = "tb_newbee_mall_goods_category"

    category_id = Column(BIGINT(20), primary_key=True, comment="分类id")
    category_level = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="分类级别(1-一级分类 2-二级分类 3-三级分类)",
    )
    parent_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="父分类id"
    )
    category_name = Column(
        String(50), nullable=False, server_default=text("''"), comment="分类名称"
    )
    category_rank = Column(
        INTEGER(11),
        nullable=False,
        server_default=text("'0'"),
        comment="排序值(字段越大越靠前)",
    )
    is_deleted = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="删除标识字段(0-未删除 1-已删除)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    create_user = Column(
        INTEGER(11), nullable=False, server_default=text("'0'"), comment="创建者id"
    )
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="修改时间",
    )
    update_user = Column(INTEGER(11), server_default=text("'0'"), comment="修改者id")


class TbNewbeeMallGoodsInfo(Base):
    __tablename__ = "tb_newbee_mall_goods_info"

    goods_id = Column(BIGINT(20), primary_key=True, comment="商品表主键id")
    goods_name = Column(
        String(200), nullable=False, server_default=text("''"), comment="商品名"
    )
    goods_intro = Column(
        String(200), nullable=False, server_default=text("''"), comment="商品简介"
    )
    goods_category_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="关联分类id"
    )
    goods_cover_img = Column(
        String(200),
        nullable=False,
        server_default=text("'/admin/dist/img/no-img.png'"),
        comment="商品主图",
    )
    goods_carousel = Column(
        String(500),
        nullable=False,
        server_default=text("'/admin/dist/img/no-img.png'"),
        comment="商品轮播图",
    )
    goods_detail_content = Column(Text, nullable=False, comment="商品详情")
    original_price = Column(
        INTEGER(11), nullable=False, server_default=text("'1'"), comment="商品价格"
    )
    selling_price = Column(
        INTEGER(11), nullable=False, server_default=text("'1'"), comment="商品实际售价"
    )
    stock_num = Column(
        INTEGER(11), nullable=False, server_default=text("'0'"), comment="商品库存数量"
    )
    tag = Column(String(20), nullable=False, server_default=text("''"), comment="商品标签")
    goods_sell_status = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="商品上架状态 1-下架 0-上架",
    )
    create_user = Column(
        INTEGER(11), nullable=False, server_default=text("'0'"), comment="添加者主键id"
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="商品添加时间",
    )
    update_user = Column(
        INTEGER(11), nullable=False, server_default=text("'0'"), comment="修改者主键id"
    )
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="商品修改时间",
    )


class TbNewbeeMallIndexConfig(Base):
    __tablename__ = "tb_newbee_mall_index_config"

    config_id = Column(BIGINT(20), primary_key=True, comment="首页配 置项主键id")
    config_name = Column(
        String(50),
        nullable=False,
        server_default=text("''"),
        comment="显示字符(配置搜索时不可为空，其他可为空)",
    )
    config_type = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="1-搜索框热搜 2-搜索下拉框热搜 3-(首页)热销商品 4-(首页)新品上线 5-(首页)为你推荐",
    )
    goods_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="商品id 默认为0"
    )
    redirect_url = Column(
        String(100),
        nullable=False,
        server_default=text("'##'"),
        comment="点击后的跳转地址(默认不跳转)",
    )
    config_rank = Column(
        INTEGER(11),
        nullable=False,
        server_default=text("'0'"),
        comment="排序值(字段越大越靠前)",
    )
    is_deleted = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="删除标识字段(0-未删除 1-已删除)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    create_user = Column(
        INTEGER(11), nullable=False, server_default=text("'0'"), comment="创建者id"
    )
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="最新修改时间",
    )
    update_user = Column(INTEGER(11), server_default=text("'0'"), comment="修改者id")


class TbNewbeeMallOrder(Base):
    __tablename__ = "tb_newbee_mall_order"

    order_id = Column(BIGINT(20), primary_key=True, comment="订单表主键id")
    order_no = Column(
        String(20), nullable=False, server_default=text("''"), comment="订单号"
    )
    user_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="用户主键id"
    )
    total_price = Column(
        INTEGER(11), nullable=False, server_default=text("'1'"), comment="订单总价"
    )
    pay_status = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="支付状态:0.未支付,1.支付成功,-1:支付失败",
    )
    pay_type = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="0.无 1.支付宝支付 2.微信支付",
    )
    pay_time = Column(DateTime, comment="支付时间")
    order_status = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="订单状态:0.待支付 1.已支付 2.配货完成 3:出库成 功 4.交易成功 -1.手动关闭 -2.超时关闭 -3.商家关闭",
    )
    extra_info = Column(
        String(100), nullable=False, server_default=text("''"), comment="订单body"
    )
    is_deleted = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="删除标识字段(0-未删除 1-已删除)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="最新修改时间",
    )


class TbNewbeeMallOrderAddres(Base):
    __tablename__ = "tb_newbee_mall_order_address"
    __table_args__ = {"comment": "订单收货地址关联表"}

    order_id = Column(BIGINT(20), primary_key=True)
    user_name = Column(
        String(30), nullable=False, server_default=text("''"), comment="收货人姓名"
    )
    user_phone = Column(
        String(11), nullable=False, server_default=text("''"), comment="收货人手机号"
    )
    province_name = Column(
        String(32), nullable=False, server_default=text("''"), comment="省"
    )
    city_name = Column(
        String(32), nullable=False, server_default=text("''"), comment="城"
    )
    region_name = Column(
        String(32), nullable=False, server_default=text("''"), comment="区"
    )
    detail_address = Column(
        String(64),
        nullable=False,
        server_default=text("''"),
        comment="收件详细地址(街道/楼宇/单元)",
    )


class TbNewbeeMallOrderItem(Base):
    __tablename__ = "tb_newbee_mall_order_item"

    order_item_id = Column(BIGINT(20), primary_key=True, comment="订 单关联购物项主键id")
    order_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="订单主键id"
    )
    goods_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="关联商品id"
    )
    goods_name = Column(
        String(200),
        nullable=False,
        server_default=text("''"),
        comment="下单时商品的名称(订单快照)",
    )
    goods_cover_img = Column(
        String(200),
        nullable=False,
        server_default=text("''"),
        comment="下单时商品的主图(订单快照)",
    )
    selling_price = Column(
        INTEGER(11),
        nullable=False,
        server_default=text("'1'"),
        comment="下单时商品的价格(订单快照)",
    )
    goods_count = Column(
        INTEGER(11),
        nullable=False,
        server_default=text("'1'"),
        comment="数量(订单快照)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )


class TbNewbeeMallShoppingCartItem(Base):
    __tablename__ = "tb_newbee_mall_shopping_cart_item"

    cart_item_id = Column(BIGINT(20), primary_key=True, comment="购物项主键id")
    user_id = Column(BIGINT(20), nullable=False, comment="用户主键id")
    goods_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="关联商品id"
    )
    goods_count = Column(
        INTEGER(11), nullable=False, server_default=text("'1'"), comment="数量(最大为5)"
    )
    is_deleted = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="删除标识字段(0-未删除 1-已删除)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="最新修改时间",
    )


class TbNewbeeMallUser(Base):
    __tablename__ = "tb_newbee_mall_user"

    user_id = Column(BIGINT(20), primary_key=True, comment="用户主键id")
    nick_name = Column(
        String(50), nullable=False, server_default=text("''"), comment="用户昵称"
    )
    login_name = Column(
        String(11),
        nullable=False,
        server_default=text("''"),
        comment="登陆名称(默认为手机号)",
    )
    password_md5 = Column(
        String(32), nullable=False, server_default=text("''"), comment="MD5加密后的密码"
    )
    introduce_sign = Column(
        String(100), nullable=False, server_default=text("''"), comment="个性签名"
    )
    is_deleted = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="注销标识字段(0-正常 1-已注销)",
    )
    locked_flag = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="锁定标识字段(0-未锁定 1-已锁定)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="注册时间",
    )


class TbNewbeeMallUserAddres(Base):
    __tablename__ = "tb_newbee_mall_user_address"
    __table_args__ = {"comment": "收货地址表"}

    address_id = Column(BIGINT(20), primary_key=True)
    user_id = Column(
        BIGINT(20), nullable=False, server_default=text("'0'"), comment="用户主键id"
    )
    user_name = Column(
        String(30), nullable=False, server_default=text("''"), comment="收货人姓名"
    )
    user_phone = Column(
        String(11), nullable=False, server_default=text("''"), comment="收货人手机号"
    )
    default_flag = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="是否为默认 0-非默认 1-是默认",
    )
    province_name = Column(
        String(32), nullable=False, server_default=text("''"), comment="省"
    )
    city_name = Column(
        String(32), nullable=False, server_default=text("''"), comment="城"
    )
    region_name = Column(
        String(32), nullable=False, server_default=text("''"), comment="区"
    )
    detail_address = Column(
        String(64),
        nullable=False,
        server_default=text("''"),
        comment="收件详细地址(街道/楼宇/单元)",
    )
    is_deleted = Column(
        TINYINT(4),
        nullable=False,
        server_default=text("'0'"),
        comment="删除标识字段(0-未删除 1-已删除)",
    )
    create_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="添加时间",
    )
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="修改时间",
    )


class TbNewbeeMallUserToken(Base):
    __tablename__ = "tb_newbee_mall_user_token"

    user_id = Column(BIGINT(20), primary_key=True, comment="用户主键id")
    token = Column(String(32), nullable=False, unique=True, comment="token值(32位字符串)")
    update_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="修改时间",
    )
    expire_time = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="token过期时间",
    )
