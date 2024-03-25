from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 创建数据库连接引擎
engine = create_engine(
    "mysql+pymysql://root:123456@localhost/newbee_mall_db_v2", echo=False
)

# 创建会话类
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
