# 修复模型测试请求日志问题

## 问题描述
后端管理端页面模型测试请求的请求内容未带上。当前测试端点 `/api/models/{model_id}/test` 只测试连通性，没有发送实际的聊天消息。

## 解决方案
修改后端测试端点，发送实际聊天请求 "你好" 并记录到日志。

## 修改内容

### backend/main.py - 修改测试端点

将 `/api/models/{model_id}/test` 端点从：
```python
@app.post("/api/models/{model_id}/test")
async def test_model_connectivity(model_id: int, db: SessionLocal = Depends(get_db)):
    """测试模型连通性"""
    success = await GatewayCore.test_connectivity(...)
```

改为：
```python
@app.post("/api/models/{model_id}/test")
async def test_model_connectivity(model_id: int, db: SessionLocal = Depends(get_db)):
    """测试模型连通性 - 发送实际聊天请求"""
    # 构建测试请求
    test_messages = [{"role": "user", "content": "你好"}]
    request_data = {
        "model": model.model_name,
        "messages": test_messages,
        "stream": False,
    }
    
    # 调用 GatewayCore 发送实际请求
    response = await GatewayCore.sync_request(
        vendor=model.vendor,
        api_base=model.api_base,
        api_key=model.api_key,
        model_name=model.model_name,
        request_data=request_data,
        db=db,
    )
    
    return {"code": 200, "msg": "连通测试成功", "data": {"response": response}}
```

## 执行步骤
1. 修改 backend/main.py 中的测试端点
2. 复制代码到 Docker 容器
3. 重启后端服务
4. 测试验证
