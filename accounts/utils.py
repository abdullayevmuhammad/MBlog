# accounts/utils.py
import random
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerificationCode, CustomUser

def send_simple_email(to_email: str, subject: str, message: str) -> None:
    """
    Oddiy text email jo'natish uchun helper.
    Hozircha console backend orqali terminalga chiqadi.
    """
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )


def generate_verification_code(user: CustomUser, purpose: str) -> EmailVerificationCode:
    """
    Berilgan user va purpose uchun 6 xonali kod yaratadi va DBga yozadi.
    """
    code = str(random.randint(100000, 999999))  # 100000–999999 oralig'ida

    expires_at = timezone.now() + timedelta(minutes=2)  # 2 daqiqaga amal qiladi

    verification = EmailVerificationCode.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=expires_at,
    )
    return verification

def send_verification_email(user: CustomUser, purpose: str):
    """
    user emailiga verification kod yuboradi.
    purpose: 'register' yoki 'reset_password'
    """
    verification = generate_verification_code(user, purpose)

    if purpose == 'register':
        subject = "Ro'yxatdan o'tishni tasdiqlash"
    elif purpose == 'reset_password':
        subject = "Parolni tiklash uchun tasdiqlash kodi"
    else:
        subject = "Tasdiqlash kodi"

    message = (
        f"Sizning tasdiqlash kodingiz: {verification.code}\n"
        f"Bu kod 2 daqiqa davomida amal qiladi."
    )

    send_simple_email(user.email, subject, message)
