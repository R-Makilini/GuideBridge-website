import hashlib

from app.core.config import settings


def generate_checkout_hash(order_id: str, amount: float, currency: str = "LKR") -> str:
    """
    PayHere checkout hash:
    hash = strtoupper( md5( merchant_id + order_id + amount + currency + strtoupper(md5(merchant_secret)) ) )
    """
    amount_str = f"{amount:.2f}"
    secret_hash = hashlib.md5(settings.PAYHERE_MERCHANT_SECRET.encode()).hexdigest().upper()
    raw = f"{settings.PAYHERE_MERCHANT_ID}{order_id}{amount_str}{currency}{secret_hash}"
    return hashlib.md5(raw.encode()).hexdigest().upper()


def verify_callback_signature(
    merchant_id: str,
    order_id: str,
    amount: str,
    currency: str,
    status_code: str,
    md5sig: str,
) -> bool:
    
    secret_hash = hashlib.md5(settings.PAYHERE_MERCHANT_SECRET.encode()).hexdigest().upper()
    raw = f"{merchant_id}{order_id}{amount}{currency}{status_code}{secret_hash}"
    expected = hashlib.md5(raw.encode()).hexdigest().upper()
    return expected == md5sig.upper()
