# 导入 APIRouter
from fastapi import APIRouter

# 创建一个路由实例（类似一个小型的 Controller）
router = APIRouter(
    prefix="/hello",  # 可选：给该路由下的所有接口加前缀（比如这里所有接口都是 /hello/xxx）
    tags=["hello模块"]  # 可选：在文档中归类显示
)

# 定义接口（类似 Controller 里的接口方法）
@router.get("/", summary="返回 hello world")
async def hello():
    return {"message": "hello world"}

@router.get("/{name}", summary="带参数的 hello")
async def hello_name(name: str):
    return {"message": f"hello {name}"}