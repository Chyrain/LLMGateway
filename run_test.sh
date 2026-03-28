#!/bin/bash
# 测试并修复 MiniMax tool_call 解析

cd /Users/chyrain/Desktop/workspace/AI/LLMGateway

# 直接运行测试
python3 << 'PYEOF'
import re
import json

# 使用转义方式构建带标签的内容
content_with_tags = "<think>\n</think>\n\n\n