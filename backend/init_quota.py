"""
初始化模型额度记录
用于修复已有模型缺少额度记录的问题
"""

from config.database import SessionLocal, init_db
from models.model_config import ModelConfig
from models.quota_stat import QuotaStat


def init_quota_records():
    """为所有没有额度记录的模型创建额度记录"""
    db = SessionLocal()
    try:
        # 获取所有模型
        models = db.query(ModelConfig).all()

        created_count = 0
        for model in models:
            # 检查是否已有额度记录
            existing = (
                db.query(QuotaStat).filter(QuotaStat.model_id == model.id).first()
            )
            if not existing:
                # 创建额度记录
                quota = QuotaStat(
                    model_id=model.id,
                    total_quota=0,
                    used_quota=0,
                    remain_quota=0,
                    used_ratio=0,
                    sync_type=0,
                )
                db.add(quota)
                created_count += 1
                print(f"✓ 已为模型 {model.vendor}/{model.model_name} 创建额度记录")

        db.commit()
        print(f"\n总计: 为 {created_count} 个模型创建了额度记录")

    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    init_quota_records()
