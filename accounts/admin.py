from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, EmailVerificationCode

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):

    list_display = ('id','email', 'first_name', 'last_name', 'is_staff')
    list_display_links = ('email',)
    ordering = ('email',)
    readonly_fields = ('date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_pic')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role')}),
        ('Important dates', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active', 'role'),
        }),
    )

    search_fields = ('email', 'first_name', 'last_name')
@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'code')
    readonly_fields = ('created_at',)