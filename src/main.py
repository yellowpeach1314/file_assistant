# server usage:
# uvicorn main:app --reload  // uvicorn src.main:app --reload

from fastapi import FastAPI
from src.api.routers import rules
from src.api.routers import documents # 导入新的 documents 路由器
from src.api.routers import file_assisant_router

# 导入数据库初始化函数 (如果需要)
# from src.documentRepository.database_models import init_db

app = FastAPI()

# init_db() # 如果需要在这里初始化数据库

app.include_router(rules.router)
app.include_router(documents.router) # 包含新的 documents 路由器
app.include_router(file_assisant_router.router)

@app.get("/")
def read_root():
    return {"Hello": "Wiki Assistant API"}

### ---- send message to the server example -----
# 上传文件
# curl -X POST http://localhost:8000/file_assistant/upload_file \
# -H "Content-Type: application/json" \
# -d '{
#     "file_path": "/path/to/your/file.txt",
#     "file_name": "your_file.txt"
# }'
