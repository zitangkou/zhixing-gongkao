from app.api.admin._deps import *  # noqa: F401,F403

router = APIRouter()


@router.post("/auth/login")
def admin_login(body: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == body.username).first()
    if not admin or not verify_password(body.password, admin.password_hash):
        return ApiResponse.fail("用户名或密码错误", code=401)
    if not admin.is_active:
        return ApiResponse.fail("账号已禁用", code=403)
    perms = parse_json(admin.role.permissions, [])
    token = create_access_token(admin.username)
    return ApiResponse.ok(
        AdminToken(
            access_token=token,
            username=admin.username,
            role=admin.role.code,
            permissions=perms,
        ).model_dump()
    )


@router.get("/auth/me")
def admin_me(admin: AdminUser = Depends(get_current_admin)):
    perms = parse_json(admin.role.permissions, [])
    return ApiResponse.ok(
        AdminUserOut(
            id=admin.id,
            username=admin.username,
            nickname=admin.nickname,
            role_code=admin.role.code,
            is_active=admin.is_active,
            created_at=admin.created_at,
            permissions=perms,
        ).model_dump()
    )
