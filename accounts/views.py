from django.shortcuts import render

# Create your views here.
from django.forms import ValidationError
from rest_framework import generics, permissions, status, views, filters
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser, FriendRequest
from .serializers import FriendRequestSerializer, User, UserCreateSerializer, UserLoginSerializer, UserSearchSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10

class CreateUserView(generics.CreateAPIView):
    model = get_user_model()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserCreateSerializer

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(**serializer.validated_data)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                "message": "Login successful"
            })
        return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class UserSearchView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSearchSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'first_name', 'last_name']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        keyword = self.request.query_params.get('search', None)
        if keyword:
            if '@' in keyword:
                return queryset.filter(email=keyword)
            else:
                return queryset.filter(first_name__icontains=keyword) | queryset.filter(last_name__icontains=keyword)
        return queryset.none()

class SendFriendRequestView(generics.CreateAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        from_user = self.request.user
        to_user = serializer.validated_data['to_user']
        key = f"{from_user.id}_requests"
        count = cache.get(key, 0)
        if count >= 3:
            raise ValidationError("Rate limit exceeded. You can only send 3 requests per minute.")
        serializer.save(from_user=from_user)
        cache.set(key, count + 1, timeout=60)

class AcceptFriendRequestView(generics.UpdateAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = FriendRequest.objects.get(id=self.kwargs['pk'])
        if obj.to_user != self.request.user:
            raise PermissionDenied()
        return obj

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.accepted = True
        instance.save()

class RejectFriendRequestView(generics.DestroyAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = FriendRequest.objects.get(id=self.kwargs['pk'])
        if obj.to_user != self.request.user:
            raise PermissionDenied()
        return obj

class FriendsListView(generics.ListAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        friend_requests = FriendRequest.objects.filter(from_user=user, accepted=True)
        return CustomUser.objects.filter(id__in=[fr.to_user.id for fr in friend_requests])

class PendingFriendRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(to_user=user, accepted=False)
