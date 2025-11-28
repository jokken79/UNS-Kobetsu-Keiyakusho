"""
Settings API Router - Company and system settings endpoints.

Provides read-only access to company (派遣元) information for contract generation.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings

router = APIRouter()


class CompanyInfo(BaseModel):
    """派遣元 company information."""
    name: str
    name_legal: str
    postal_code: str
    address: str
    full_address: str
    tel: str
    mobile: str
    fax: Optional[str] = None
    email: str
    website: str


class LicenseInfo(BaseModel):
    """Company licenses."""
    dispatch_license: str  # 労働者派遣事業
    support_org: str  # 登録支援機関
    job_placement: str  # 有料職業紹介事業


class ManagerInfo(BaseModel):
    """派遣元責任者 information."""
    name: str
    position: str


class CompanySettings(BaseModel):
    """Full company settings response."""
    company: CompanyInfo
    licenses: LicenseInfo
    manager: ManagerInfo


@router.get("/company", response_model=CompanySettings)
async def get_company_settings():
    """
    Get 派遣元 (dispatch source company) information.

    This endpoint returns UNS-Kikaku company details used in contracts
    and official documents.
    """
    return CompanySettings(
        company=CompanyInfo(
            name=settings.COMPANY_NAME,
            name_legal=settings.COMPANY_NAME_LEGAL,
            postal_code=settings.COMPANY_POSTAL_CODE,
            address=settings.COMPANY_ADDRESS,
            full_address=f"〒{settings.COMPANY_POSTAL_CODE} {settings.COMPANY_ADDRESS}",
            tel=settings.COMPANY_TEL,
            mobile=settings.COMPANY_MOBILE,
            fax=settings.COMPANY_FAX or "",
            email=settings.COMPANY_EMAIL,
            website=settings.COMPANY_WEBSITE,
        ),
        licenses=LicenseInfo(
            dispatch_license=settings.COMPANY_LICENSE_NUMBER,
            support_org=settings.COMPANY_SUPPORT_ORG_NUMBER,
            job_placement=settings.COMPANY_JOB_PLACEMENT_NUMBER,
        ),
        manager=ManagerInfo(
            name=settings.DISPATCH_MANAGER_NAME,
            position=settings.DISPATCH_MANAGER_POSITION,
        ),
    )


@router.get("/system")
async def get_system_info():
    """Get basic system information."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
