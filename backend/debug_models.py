#!/usr/bin/env python3
"""
调试脚本：检查模型数据
"""

import sys

sys.path.insert(0, "/Users/chyrain/Desktop/workspace/AI/LLMGateway/backend")

from config.database import SessionLocal, init_db
from models.model_config import ModelConfig
from config.encryption import decrypt_api_key


def check_models():
    db = SessionLocal()
    try:
        models = db.query(ModelConfig).all()
        print(f"共有 {len(models)} 个模型\n")

        for model in models:
            print(f"模型 ID: {model.id}")
            print(f"  厂商: {model.vendor}")
            print(f"  名称: {model.model_name}")
            print(f"  优先级: {model.priority}")
            print(f"  API Key 是否存在: {bool(model.api_key)}")
            if model.api_key:
                try:
                    decrypted = decrypt_api_key(model.api_key)
                    print(
                        f"  API Key (解密后): {decrypted[:10]}...{decrypted[-5:] if len(decrypted) > 15 else ''}"
                    )
                except Exception as e:
                    print(f"  API Key 解密失败: {e}")
            else:
                print(f"  API Key: 空")
            print()

    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    check_models()
