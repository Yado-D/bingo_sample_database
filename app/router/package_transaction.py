from fastapi import APIRouter, status

router = APIRouter(tags=["Package Transaction"], prefix="/package")


@router.get("/", status_code=status.HTTP_410_GONE)
def deprecated_package_api():
    return {"status": "error", "message": "This package API is deprecated. Use /transactions endpoints instead."}


    if user.role.value == "OWNER":
        return package_transaction

    package_transactions = (
        db.query(models.PackageTransaction)
        .filter(
            or_(
                models.PackageTransaction.receiver_id == id,
                models.PackageTransaction.sender_id == id,
            )
        )
        .all()
    )
    if not package_transactions:
        raise HTTPException(
            status_code=404, detail="you don't have a package transaction yet."
        )

    return package_transactions
