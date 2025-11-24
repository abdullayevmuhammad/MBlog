from django.contrib.auth import authenticate
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from .utils import send_verification_email
from .models import CustomUser, EmailVerificationCode, Follow
from .serializers import (
    CustomUserRegisterSerializer,
    CustomUserProfileSerializer,
    EmailVerificationSerializer,
    UserShortProfileSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer
)
from django.db import models

class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = CustomUserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # user yaratamiz, lekin is_active=False qilamiz
        user = serializer.save()
        user.is_active = False
        user.save()

        # Token yaratamiz (hozir login uchun zarur bo'lmasa ham, qoldirish mumkin yoki olib tashlash mumkin)
        token, created = Token.objects.get_or_create(user=user)

        # Emailga verification kod yuboramiz
        send_verification_email(user, purpose='register')

        data = {
            "user": CustomUserProfileSerializer(user).data,
            "token": token.key,
            "detail": "Ro'yxatdan o'tdingiz. Emailga tasdiqlash kodi yuborildi."
        }
        return Response(data, status=status.HTTP_201_CREATED)

        
class LoginViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "detail": "Email and password are required.",
                    "malumot": "Email va parol kiritilishi kerak."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response(
                {
                    "detail": "Email or password is incorrect.",
                    "malumot": "Email yoki parol noto'g'ri."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Email verify bo'lmagan bo'lsa, login bermaymiz
        if not user.is_active:
            return Response(
                {
                    "detail": "Account is not active. Please verify your email.",
                    "malumot": "Profil hali faollashtirilmagan. Emailingizni tasdiqlang."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        token, created = Token.objects.get_or_create(user=user)

        data = {
            "user": CustomUserProfileSerializer(user).data,
            "token": token.key,
        }
        return Response(data, status=status.HTTP_200_OK)


class LogoutViewSet(viewsets.ViewSet):

    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        # request.auth — bu aynan Token instance bo'ladi
        token = request.auth
        if token:
            token.delete()
        return Response({"detail": "Successfully logged out", "ma'lumot": "Profildan muvaffaqiyatli chiqildi."}, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # adminlar hammani ko'radi
        if user.is_staff or user.is_superuser:
            return CustomUser.objects.all()
        # oddiy user faqat o'zini ko'radi
        return CustomUser.objects.filter(is_active=True)
    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Yangi user yaratish faqat /api/auth/register orqali mumkin."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):

        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method == "PATCH":
            serializer = self.get_serializer(user, data=request.data, partial=True) # partial=True -> faqat berilgan maydonlarni o'zgartirish
            serializer.is_valid(raise_exception=True) # raise_exception=True -> xato bo'lsa 400 xato qaytaradi
            serializer.save()
            return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="me/followers")
    def my_followers(self, request):
        user = request.user

        follow_qs = Follow.objects.filter(
            following=user
        ).select_related("follower")

        followers_users = [f.follower for f in follow_qs]

        serializer = UserShortProfileSerializer(followers_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["get"], url_path="me/following")
    def my_following(self, request):
        user = request.user

        follow_qs = Follow.objects.filter(
            follower=user
        ).select_related("following")

        following_users = [f.following for f in follow_qs]

        serializer = UserShortProfileSerializer(following_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"], url_path="follow")
    def follow(self, request, pk=None):
        me = request.user

        try:
            target = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        # O'zini follow qila olmaydi
        if me.id == target.id:
            return Response(
                {"detail": "O'zingizni follow qila olmaysiz."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Allaqachon follow qilingan bo'lsa
        follow_obj, created = Follow.objects.get_or_create(
            follower=me,
            following=target,
        )

        if not created:
            return Response(
                {"detail": "Siz bu foydalanuvchini allaqachon follow qilgansiz."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Foydalanuvchini follow qildingiz."},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["delete"], url_path="unfollow")
    def unfollow(self, request, pk=None):
        """
        Hozirgi user -> pk dagi userni unfollow qiladi.
        URL: DELETE /api/users/{id}/unfollow/
        """
        me = request.user

        try:
            target = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        if me.id == target.id:
            return Response(
                {"detail": "O'zingizni unfollow qila olmaysiz."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = Follow.objects.filter( # 
            follower=me,
            following=target,
        ).delete()

        if deleted_count == 0:
            return Response(
                {"detail": "Siz bu foydalanuvchini follow qilmagansiz."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Unfollow qilindi."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["get"], url_path="followers")
    def followers(self, request, pk=None):

        try:
            target = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Follow jadvalidan olamiz:
        # following = target bo'lgan qatorlar -> follower userlar
        follow_qs = Follow.objects.filter( 
            following=target
        ).select_related("follower")

        followers_users = [f.follower for f in follow_qs]

        serializer = UserShortProfileSerializer(followers_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="following")
    def following(self, request, pk=None):
        """
        Berilgan user kimlarni follow qilayotgani ro'yxati.
        URL: GET /api/users/{id}/following/
        """
        try:
            target = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "User topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        # follower = target bo'lgan qatorlar -> following userlar
        follow_qs = Follow.objects.filter(
            follower=target
        ).select_related("following")

        following_users = [f.following for f in follow_qs]

        serializer = UserShortProfileSerializer(following_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EmailVerifyViewSet(viewsets.ViewSet):

    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Bunday email bilan user topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Eng oxirgi (yangi) verification kodni olamiz
        verification_qs = EmailVerificationCode.objects.filter(
            user=user,
            code=code,
            purpose='register',
            is_used=False,
        ).order_by('-created_at')

        verification = verification_qs.first()

        if not verification:
            return Response(
                {"detail": "Kod noto'g'ri yoki allaqachon ishlatilgan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verification.is_expired():
            return Response(
                {"detail": "Kodning amal qilish muddati tugagan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Hammasi yaxshi -> kodni ishlatilgan deb belgilaymiz, userni faollashtiramiz
        verification.is_used = True
        verification.save()

        user.is_active = True
        user.save()

        return Response(
            {"detail": "Email muvaffaqiyatli tasdiqlandi."},
            status=status.HTTP_200_OK
        )

class PasswordResetViewSet(viewsets.ViewSet):

    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'], url_path='request')
    def request_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Xavfsizlik uchun "user yo'q" deb aytmaslik ham mumkin,
            # hozircha sodda holda yozamiz
            return Response(
                {"detail": "Bunday email bilan user topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Emailga reset_password purpose bilan kod yuboramiz
        send_verification_email(user, purpose='reset_password')

        return Response(
            {"detail": "Parolni tiklash uchun kod emailga yuborildi."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='confirm')
    def confirm_reset(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['password1']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Bunday email bilan user topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

        verification_qs = EmailVerificationCode.objects.filter(
            user=user,
            code=code,
            purpose='reset_password',
            is_used=False,
        ).order_by('-created_at')

        verification = verification_qs.first()

        if not verification:
            return Response(
                {"detail": "Kod noto'g'ri yoki allaqachon ishlatilgan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verification.is_expired():
            return Response(
                {"detail": "Kodning amal qilish muddati tugagan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Kodni ishlatilgan deb belgilaymiz
        verification.is_used = True
        verification.save()

        # Parolni o'zgartiramiz
        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Parol muvaffaqiyatli o'zgartirildi."},
            status=status.HTTP_200_OK
        )


class UsersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Foydalanuvchilar ro'yxatini ko'rish va bitta foydalanuvchi haqida ma'lumot olish.
    Faqat o'qish uchun.
    """
    queryset = CustomUser.objects.filter(is_active=True)
    serializer_class = UserShortProfileSerializer
    # permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.query_params.get("q")

        if q:
            queryset = queryset.filter(
                models.Q(first_name__icontains=q) |
                models.Q(last_name__icontains=q) |
                models.Q(email__icontains=q)
            )
        return queryset