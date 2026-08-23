from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import require_permission
from app.core.response import ApiResponse
from app.database import get_db
from app.models import ContentOperationTemplate, ContentPublishPackage
from app.schemas import ContentPublishPackageCreate, ContentPublishStatusBody
from app.services.content_ops_service import create_package, package_out, template_out, transition_package

router = APIRouter()


@router.get("/content-ops/templates")
def templates(productKey: str | None = None, _admin=Depends(require_permission("content_ops:read")), db: Session = Depends(get_db)):
    query = db.query(ContentOperationTemplate).filter(ContentOperationTemplate.status == "enabled")
    if productKey:
        query = query.filter(ContentOperationTemplate.product_key.in_([productKey, "general"]))
    rows = query.order_by(ContentOperationTemplate.sort_order, ContentOperationTemplate.created_at).all()
    return ApiResponse.ok([template_out(row) for row in rows])


@router.get("/content-ops/packages")
def packages(status: str | None = None, productKey: str | None = None, _admin=Depends(require_permission("content_ops:read")), db: Session = Depends(get_db)):
    query = db.query(ContentPublishPackage)
    if status: query = query.filter(ContentPublishPackage.status == status)
    if productKey: query = query.filter(ContentPublishPackage.product_key == productKey)
    rows = query.order_by(ContentPublishPackage.created_at.desc()).limit(200).all()
    return ApiResponse.ok([package_out(row) for row in rows])


@router.post("/content-ops/packages")
def package_create(body: ContentPublishPackageCreate, _admin=Depends(require_permission("content_ops:write")), db: Session = Depends(get_db)):
    try: return ApiResponse.ok(create_package(db, body))
    except ValueError as exc: return ApiResponse.fail(str(exc), code=400)


@router.post("/content-ops/packages/{package_id}/status")
def package_status(package_id: str, body: ContentPublishStatusBody, _admin=Depends(require_permission("content_ops:write")), db: Session = Depends(get_db)):
    try: return ApiResponse.ok(transition_package(db, package_id, body.status, body.reviewNote))
    except ValueError as exc: return ApiResponse.fail(str(exc), code=400)
