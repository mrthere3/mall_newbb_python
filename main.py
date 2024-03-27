from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api import mall_carousel, mall_goods_info, mall_goods_category, mall_order


app = FastAPI()
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(mall_carousel.route, tags=["Carousels"])
app.include_router(mall_goods_info.route, tags=["good_info"])
app.include_router(mall_goods_category.route, tags=["category"])
app.include_router(mall_order.order_route, tags=["order"])


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8888)
