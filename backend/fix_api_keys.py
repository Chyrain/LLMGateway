#!/usr/bin/env python3
"""
修复脚本：将数据库中加密的 API Key 解密为明文
"""

import sys

sys.path.insert(0, "/Users/chyrain/Desktop/workspace/AI/LLMGateway/backend")

from config.database import SessionLocal, init_db
from models.model_config import ModelConfig
from config.encryption import decrypt_api_key


def fix_encrypted_keys():
    db = SessionLocal()
    try:
        models = db.query(ModelConfig).all()
        print(f"共有 {len(models)} 个模型需要检查\n")

        fixed_count = 0
        for model in models:
            if model.api_key:
                try:
                    # 尝试解密
                    decrypted = decrypt_api_key(model.api_key)
                    # 更新为明文
                    model.api_key = decrypted
                    fixed_count += 1
                    print(
                        f"✓ 模型 {model.id} ({model.vendor}/{model.model_name}): 已解密"
                    )
                except Exception as e:
                    # 如果解密失败，说明可能已经是明文，或者加密有问题
                    print(
                        f"✗ 模型 {model.id} ({model.vendor}/{model.model_name}): 解密失败或已是明文 - {e}"
                    )
            else:
                print(
                    f"- 模型 {model.id} ({model.vendor}/{model.model_name}): 无 API Key"
                )

        if fixed_count > 0:
            db.commit()
            print(f"\n成功修复 {fixed_count} 个模型")
        else:
            print("\n无需修复")

    except Exception as e:
        db.rollback()
        print(f"修复失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    fix_encrypted_keys()
