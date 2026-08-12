"""初始化数据库种子数据"""

import json

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import hash_password
from app.models import AdminUser, RechargePackage, Role, SystemSetting
from app.services.category_service import seed_default_categories
from app.services.featured_article import seed_featured_article

settings = get_settings()


def seed_if_empty(db: Session) -> None:
    if db.query(Role).count() == 0:
        for code, perms in ROLE_PERMISSIONS.items():
            names = {"super_admin": "超级管理员", "editor": "编辑", "viewer": "只读"}
            db.add(Role(code=code, name=names.get(code, code), permissions=json.dumps(perms)))

    db.flush()

    if db.query(AdminUser).count() == 0:
        role = db.query(Role).filter(Role.code == "super_admin").first()
        db.add(AdminUser(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            nickname="系统管理员",
            role_id=role.id,
        ))

    if db.query(RechargePackage).count() == 0:
        db.add_all([
            RechargePackage(label="入门包", points=100, price=600, sort_order=1),
            RechargePackage(label="进阶包", points=500, price=2800, sort_order=2),
            RechargePackage(label="学霸包", points=1000, price=5000, sort_order=3),
            RechargePackage(label="尊享包", points=2000, price=8800, sort_order=4),
        ])

    if db.query(SystemSetting).count() == 0:
        defaults = [
            ("site_name", "知行", "站点名称"),
            ("points_sign_base", "5", "签到基础积分"),
            ("points_read_article", "3", "阅读文章积分"),
            ("points_correct_answer", "2", "答对题目积分"),
            ("crawl_enabled", "false", "是否启用定时爬虫（暂关闭）"),
        ]
        for key, value, desc in defaults:
            db.add(SystemSetting(key=key, value=value, description=desc))

    db.commit()

    seed_default_categories(db)
    db.commit()

    seed_featured_article(db)
    db.commit()

    from app.services.rmrb_meta_service import ensure_rmrb_meta_defaults

    ensure_rmrb_meta_defaults(db)
