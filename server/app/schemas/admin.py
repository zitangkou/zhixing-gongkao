"""Pydantic schema · 域模块

按业务域拆分，统一由 app/schemas/__init__.py re-export，保持 from app.schemas import X 兼容。
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
class AdminLogin(BaseModel):
    username: str
    password: str


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    permissions: list[str]


class AdminUserOut(BaseModel):
    id: int
    username: str
    nickname: str
    role_code: str
    is_active: bool
    created_at: datetime
    permissions: list[str] = []


class AppUserOut(BaseModel):
    id: str
    nickname: str
    avatar: str
    points: int
    is_member: bool
    is_active: bool
    created_at: datetime


class AppUserUpdate(BaseModel):
    nickname: str | None = None
    points: int | None = None
    is_member: bool | None = None
    is_active: bool | None = None


class SettingOut(BaseModel):
    key: str
    value: str
    description: str


class SettingUpdate(BaseModel):
    value: str


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    permissions: list[str]


# ===== 每日学习清单 =====


