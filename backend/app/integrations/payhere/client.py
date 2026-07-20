from app.core.config import settings
from app.integrations.payhere.schemas import PayHereCheckoutPayload
from app.integrations.payhere.signatures import generate_checkout_hash

PAYHERE_SANDBOX_URL = "https://sandbox.payhere.lk/pay/checkout"
PAYHERE_LIVE_URL = "https://www.payhere.lk/pay/checkout"


def build_checkout_payload(
    order_id: str,
    amount: float,
    items_description: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    address: str = "N/A",
    city: str = "Colombo",
    country: str = "Sri Lanka",
    currency: str = "LKR",
) -> PayHereCheckoutPayload:
    checkout_hash = generate_checkout_hash(order_id, amount, currency)
    return PayHereCheckoutPayload(
        merchant_id=settings.PAYHERE_MERCHANT_ID,
        return_url=f"{settings.FRONTEND_URL}/payments/return",
        cancel_url=f"{settings.FRONTEND_URL}/payments/cancel",
        notify_url=settings.PAYHERE_NOTIFY_URL,
        order_id=order_id,
        items=items_description,
        currency=currency,
        amount=f"{amount:.2f}",
        hash=checkout_hash,
        first_name=first_name,
        last_name=last_name or ".",
        email=email,
        phone=phone or "0000000000",
        address=address,
        city=city,
        country=country,
        sandbox=settings.PAYHERE_SANDBOX,
    )


def checkout_endpoint() -> str:
    return PAYHERE_SANDBOX_URL if settings.PAYHERE_SANDBOX else PAYHERE_LIVE_URL
