from django.urls import path
from accounts.views import AcceptFriendRequestView, CreateUserView, FriendsListView, LoginView, PendingFriendRequestsView, RejectFriendRequestView, SendFriendRequestView, UserSearchView

urlpatterns = [
    path('register/', CreateUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('send-request/', SendFriendRequestView.as_view(), name='send_request'),
    path('accept-request/<int:pk>/', AcceptFriendRequestView.as_view(), name='accept_request'),
    path('reject-request/<int:pk>/', RejectFriendRequestView.as_view(), name='reject_request'),
    path('friends/', FriendsListView.as_view(), name='friends_list'),
    path('pending-requests/', PendingFriendRequestsView.as_view(), name='pending_requests'),
]
