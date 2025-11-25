"""
Kobetsu Keiyakusho API Router

個別契約書 (Individual Contract) endpoints for managing dispatch contracts
under 労働者派遣法第26条 (Worker Dispatch Law Article 26).

Provides 24 endpoints for full contract lifecycle management.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.services.kobetsu_service import KobetsuService
from app.services.kobetsu_pdf_service import KobetsuPDFService
from app.schemas.kobetsu_keiyakusho import (
    KobetsuKeiyakushoCreate,
    KobetsuKeiyakushoUpdate,
    KobetsuKeiyakushoResponse,
    KobetsuKeiyakushoList,
    KobetsuKeiyakushoStats,
)

router = APIRouter()


# ========================================
# LIST & SEARCH ENDPOINTS
# ========================================

@router.get("/", response_model=dict)
async def list_contracts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    factory_id: Optional[int] = Query(None, description="Filter by factory"),
    search: Optional[str] = Query(None, description="Search in contract number and worksite"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get paginated list of Kobetsu Keiyakusho contracts.

    Returns list of contracts with pagination metadata.
    Supports filtering by status, factory, date range, and text search.
    """
    service = KobetsuService(db)
    contracts, total = service.get_list(
        skip=skip,
        limit=limit,
        status=status,
        factory_id=factory_id,
        search=search,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "items": [KobetsuKeiyakushoList.model_validate(c) for c in contracts],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(contracts) < total,
    }


@router.get("/stats", response_model=KobetsuKeiyakushoStats)
async def get_statistics(
    factory_id: Optional[int] = Query(None, description="Filter by factory"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get contract statistics.

    Returns counts of contracts by status, expiring soon count,
    and total workers in active contracts.
    """
    service = KobetsuService(db)
    return service.get_stats(factory_id=factory_id)


@router.get("/expiring", response_model=List[KobetsuKeiyakushoList])
async def get_expiring_contracts(
    days: int = Query(30, ge=1, le=365, description="Days until expiration"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get contracts expiring within specified days.

    Useful for renewal planning and notifications.
    """
    service = KobetsuService(db)
    contracts = service.get_expiring_contracts(days=days)
    return [KobetsuKeiyakushoList.model_validate(c) for c in contracts]


@router.get("/by-factory/{factory_id}", response_model=List[KobetsuKeiyakushoList])
async def get_contracts_by_factory(
    factory_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all contracts for a specific factory.
    """
    service = KobetsuService(db)
    contracts = service.get_by_factory(factory_id)
    return [KobetsuKeiyakushoList.model_validate(c) for c in contracts]


@router.get("/by-employee/{employee_id}", response_model=List[KobetsuKeiyakushoList])
async def get_contracts_by_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all contracts for a specific employee.
    """
    service = KobetsuService(db)
    contracts = service.get_by_employee(employee_id)
    return [KobetsuKeiyakushoList.model_validate(c) for c in contracts]


# ========================================
# CRUD ENDPOINTS
# ========================================

@router.post("/", response_model=KobetsuKeiyakushoResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    data: KobetsuKeiyakushoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new Kobetsu Keiyakusho (個別契約書).

    Creates a contract in 'draft' status with all 16 legally required items
    as defined in 労働者派遣法第26条.

    Required fields include:
    - 業務内容 (work content)
    - 派遣期間 (dispatch period)
    - 就業時間 (work hours)
    - 派遣料金 (dispatch fee)
    - 責任者情報 (manager information)
    - And more...
    """
    service = KobetsuService(db)

    try:
        contract = service.create(data, created_by=current_user.get("id"))
        return KobetsuKeiyakushoResponse.model_validate(contract)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{contract_id}", response_model=KobetsuKeiyakushoResponse)
async def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific contract by ID.

    Returns full contract details including all 16 legally required items.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.get("/by-number/{contract_number}", response_model=KobetsuKeiyakushoResponse)
async def get_contract_by_number(
    contract_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific contract by contract number.

    Contract number format: KOB-YYYYMM-XXXX (e.g., KOB-202411-0001)
    """
    service = KobetsuService(db)
    contract = service.get_by_contract_number(contract_number)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract {contract_number} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.put("/{contract_id}", response_model=KobetsuKeiyakushoResponse)
async def update_contract(
    contract_id: int,
    data: KobetsuKeiyakushoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update an existing contract.

    Only modifiable fields can be updated. Some fields may be
    restricted based on contract status.
    """
    service = KobetsuService(db)
    contract = service.update(contract_id, data)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: int,
    hard: bool = Query(False, description="Permanently delete (only for drafts)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a contract.

    By default, performs soft delete (changes status to 'cancelled').
    Use hard=true to permanently delete (only works for draft contracts).
    """
    service = KobetsuService(db)

    if hard:
        success = service.hard_delete(contract_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot permanently delete: contract not found or not a draft"
            )
    else:
        success = service.delete(contract_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract with ID {contract_id} not found"
            )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ========================================
# STATUS MANAGEMENT ENDPOINTS
# ========================================

@router.post("/{contract_id}/activate", response_model=KobetsuKeiyakushoResponse)
async def activate_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Activate a draft contract.

    Changes status from 'draft' to 'active'.
    Only draft contracts can be activated.
    """
    service = KobetsuService(db)
    contract = service.activate(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate: contract not found or not a draft"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.post("/{contract_id}/renew", response_model=KobetsuKeiyakushoResponse)
async def renew_contract(
    contract_id: int,
    new_end_date: date = Query(..., description="New dispatch end date"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Renew a contract with a new end date.

    Creates a new contract based on the original, with:
    - New contract number
    - Start date = original end date + 1 day
    - End date = specified new_end_date
    - Status = 'draft'

    Original contract status is changed to 'renewed'.
    """
    service = KobetsuService(db)
    contract = service.renew(
        contract_id,
        new_end_date=new_end_date,
        created_by=current_user.get("id")
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot renew: contract not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


@router.post("/{contract_id}/duplicate", response_model=KobetsuKeiyakushoResponse)
async def duplicate_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a copy of an existing contract.

    Creates a new draft contract with:
    - New contract number
    - Same data as original
    - Status = 'draft'
    """
    service = KobetsuService(db)
    contract = service.duplicate(contract_id, created_by=current_user.get("id"))

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return KobetsuKeiyakushoResponse.model_validate(contract)


# ========================================
# EMPLOYEE MANAGEMENT ENDPOINTS
# ========================================

@router.get("/{contract_id}/employees", response_model=List[int])
async def get_contract_employees(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of employee IDs associated with a contract.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return service.get_employees(contract_id)


@router.post("/{contract_id}/employees/{employee_id}", status_code=status.HTTP_201_CREATED)
async def add_employee_to_contract(
    contract_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Add an employee to a contract.
    """
    service = KobetsuService(db)
    success = service.add_employee(contract_id, employee_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add employee: contract not found or employee already assigned"
        )

    return {"message": f"Employee {employee_id} added to contract {contract_id}"}


@router.delete("/{contract_id}/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_employee_from_contract(
    contract_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Remove an employee from a contract.
    """
    service = KobetsuService(db)
    success = service.remove_employee(contract_id, employee_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove employee: contract or employee not found"
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ========================================
# DOCUMENT GENERATION ENDPOINTS
# ========================================

@router.post("/{contract_id}/generate-pdf")
async def generate_contract_pdf(
    contract_id: int,
    format: str = Query("pdf", description="Output format: pdf or docx"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate PDF or DOCX document for a contract.

    Returns the generated document file.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    pdf_service = KobetsuPDFService()

    try:
        if format == "docx":
            file_path = pdf_service.generate_docx(contract)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{contract.contract_number}.docx"
        else:
            file_path = pdf_service.generate_pdf(contract)
            media_type = "application/pdf"
            filename = f"{contract.contract_number}.pdf"

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )


@router.post("/{contract_id}/sign")
async def sign_contract(
    contract_id: int,
    pdf_path: str = Query(..., description="Path to signed PDF"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a contract as signed and store the signed PDF path.
    """
    service = KobetsuService(db)
    contract = service.sign_contract(contract_id, pdf_path)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    return {
        "message": "Contract signed successfully",
        "signed_date": contract.signed_date,
        "pdf_path": contract.pdf_path,
    }


@router.get("/{contract_id}/download")
async def download_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Download the signed PDF for a contract.
    """
    service = KobetsuService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found"
        )

    if not contract.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No signed PDF available for this contract"
        )

    return FileResponse(
        path=contract.pdf_path,
        media_type="application/pdf",
        filename=f"{contract.contract_number}_signed.pdf",
    )


# ========================================
# ADMIN ENDPOINTS
# ========================================

@router.post("/update-expired", dependencies=[Depends(require_role("admin"))])
async def update_expired_contracts(
    db: Session = Depends(get_db),
):
    """
    Update status of expired contracts.

    Admin-only endpoint that should be called by a scheduled task.
    Marks all active contracts past their end date as 'expired'.
    """
    service = KobetsuService(db)
    count = service.update_expired_contracts()

    return {
        "message": f"Updated {count} expired contracts",
        "count": count,
    }


@router.get("/export/csv")
async def export_contracts_csv(
    status: Optional[str] = Query(None, description="Filter by status"),
    factory_id: Optional[int] = Query(None, description="Filter by factory"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Export contracts to CSV format.
    """
    service = KobetsuService(db)
    contracts, _ = service.get_list(
        skip=0,
        limit=10000,  # Max export
        status=status,
        factory_id=factory_id,
    )

    # Generate CSV content
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "契約番号", "派遣先名", "開始日", "終了日", "労働者数", "ステータス", "作成日"
    ])

    # Data rows
    for c in contracts:
        writer.writerow([
            c.contract_number,
            c.worksite_name,
            c.dispatch_start_date.isoformat(),
            c.dispatch_end_date.isoformat(),
            c.number_of_workers,
            c.status,
            c.created_at.isoformat(),
        ])

    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=kobetsu_contracts.csv"
        }
    )
