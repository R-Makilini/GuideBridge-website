def verification_email_html(full_name: str, otp_code: str, verify_link: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto">
      <h2>Welcome to GuideBridge, {full_name}!</h2>
      <p>Your email verification code is:</p>
      <h1 style="letter-spacing:4px">{otp_code}</h1>
      <p>Or click the link below to verify your account:</p>
      <p><a href="{verify_link}">{verify_link}</a></p>
      <p>This code expires in 30 minutes.</p>
    </div>
    """


def password_reset_email_html(full_name: str, reset_link: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto">
      <h2>Password Reset Requested</h2>
      <p>Hi {full_name}, click the link below to reset your GuideBridge password:</p>
      <p><a href="{reset_link}">{reset_link}</a></p>
      <p>If you did not request this, please ignore this email. The link expires in 1 hour.</p>
    </div>
    """


def generic_notification_html(title: str, body: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto">
      <h2>{title}</h2>
      <p>{body}</p>
    </div>
    """
