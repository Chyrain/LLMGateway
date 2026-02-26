# 修复请求日志和图片错误问题

## 问题描述

1. **request_content 字段为空** - 日志详情中没有显示发送的内容（如"你好"）
2. **图片错误提示问题** - 前端显示了不应该显示的技术错误信息

## 修复任务

### Task 1: 调试并修复 request_content 保存问题

**问题分析**:
- 代码逻辑正确但数据库中 request_content 为 None
- 需要添加调试代码定位问题

**修复方案**:
- 在日志记录处添加调试输出
- 重新构建并部署
- 验证 request_content 正确保存

### Task 2: 修复前端错误信息显示问题

**问题分析**:
- 用户看到了技术性错误信息: "ERROR: Cannot read "image.png" (this model does not support image input). Inform the user."
- 这类内部错误信息不应该暴露给用户

**修复方案**:
- 修改后端错误处理，返回用户友好的错误信息
- 或在前端添加错误信息过滤

## 验证步骤

1. 发送测试请求
2. 检查数据库 request_content 字段
3. 检查前端日志详情显示
