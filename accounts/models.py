from django.contrib.auth.models import UserManager , PermissionsMixin, AbstractBaseUser
from django.db import models
from django.utils import timezone

class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set | Email kiritilishi kerak')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        return self._create_user(email, password, **extra_fields)


    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email, password, **extra_fields)

admin, user = 'admin', 'user'



class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        (admin, admin),
        (user, user),
    )
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES, default='user')

    profile_pic = models.ImageField(upload_to='user/profile_pic/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_full_name(self):
        if self.first_name and self.last_name:
            return self.first_name + ' ' + self.last_name
        return self.email.split('@')[0].title()

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]

    def __str__(self):
        return self.email

class EmailVerificationCode(models.Model):
    PURPOSE_CHOICES = (
        ('register', 'Register'),
        ('reset_password', 'Reset password'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_codes')
    code = models.CharField(max_length=6)  # masalan: "123456"
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.code}"

class Follow(models.Model):
    
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followings')
    following = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # bitta user bitta userni faqat bir marta follow qila oladi
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.email} -> {self.following.email}"