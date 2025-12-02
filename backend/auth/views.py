"""
Authentication views with MFA support
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import match_token
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64

from .models import UserProfile, AuditLog, LoginAttempt
from .serializers import UserSerializer, AuditLogSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login endpoint with MFA support"""
    username = request.data.get('username')
    password = request.data.get('password')
    mfa_token = request.data.get('mfa_token')

    # Log attempt
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Authenticate
    user = authenticate(username=username, password=password)

    if not user:
        LoginAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=False,
            failure_reason='Invalid credentials'
        )
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check if MFA is enabled
    profile = user.profile
    if profile.mfa_enabled or profile.mfa_enforced:
        if not mfa_token:
            return Response({
                'mfa_required': True,
                'message': 'MFA token required'
            }, status=status.HTTP_200_OK)

        # Verify MFA token
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if not device or not device.verify_token(mfa_token):
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                successful=False,
                failure_reason='Invalid MFA token'
            )
            return Response(
                {'error': 'Invalid MFA token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    # Success - generate tokens
    refresh = RefreshToken.for_user(user)

    LoginAttempt.objects.create(
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        successful=True
    )

    AuditLog.objects.create(
        user=user,
        username=username,
        action=AuditLog.Action.LOGIN,
        resource_type='user',
        description=f'User {username} logged in',
        ip_address=ip_address,
        user_agent=user_agent
    )

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout endpoint"""
    AuditLog.objects.create(
        user=request.user,
        username=request.user.username,
        action=AuditLog.Action.LOGOUT,
        resource_type='user',
        description=f'User {request.user.username} logged out',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    return Response({'message': 'Logged out successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_mfa(request):
    """Setup MFA for user"""
    user = request.user

    # Create or get TOTP device
    device = TOTPDevice.objects.filter(user=user).first()
    if not device:
        device = TOTPDevice.objects.create(
            user=user,
            name=f'{user.username}-device',
            confirmed=False
        )

    # Generate QR code
    url = device.config_url
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code = base64.b64encode(buffered.getvalue()).decode()

    return Response({
        'secret': device.key,
        'qr_code': f'data:image/png;base64,{qr_code}',
        'url': url
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_mfa(request):
    """Verify and enable MFA"""
    token = request.data.get('token')

    device = TOTPDevice.objects.filter(user=request.user).first()
    if not device:
        return Response(
            {'error': 'MFA not set up'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if device.verify_token(token):
        device.confirmed = True
        device.save()

        profile = request.user.profile
        profile.mfa_enabled = True
        profile.save()

        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            action=AuditLog.Action.UPDATE,
            resource_type='user',
            description='MFA enabled',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({'message': 'MFA enabled successfully'})

    return Response(
        {'error': 'Invalid token'},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_mfa(request):
    """Disable MFA (requires current MFA token)"""
    token = request.data.get('token')

    device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    if not device:
        return Response(
            {'error': 'MFA not enabled'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if device.verify_token(token):
        device.delete()

        profile = request.user.profile
        profile.mfa_enabled = False
        profile.save()

        AuditLog.objects.create(
            user=request.user,
            username=request.user.username,
            action=AuditLog.Action.UPDATE,
            resource_type='user',
            description='MFA disabled',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({'message': 'MFA disabled successfully'})

    return Response(
        {'error': 'Invalid token'},
        status=status.HTTP_400_BAD_REQUEST
    )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log viewing"""
    queryset = AuditLog.objects.select_related('user')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        return queryset
