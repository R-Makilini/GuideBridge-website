from pydantic import BaseModel


class PayHereCheckoutPayload(BaseModel):
    merchant_id: str
    return_url: str
    cancel_url: str
    notify_url: str
    order_id: str
    items: str
    currency: str
    amount: str
    hash: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    city: str
    country: str
    sandbox: bool


class PayHereCallback(BaseModel):
    merchant_id: str
    order_id: str
    payment_id: str
    payhere_amount: str
    payhere_currency: str
    status_code: str
    md5sig: str
    method: str | None = None
    status_message: str | None = None
