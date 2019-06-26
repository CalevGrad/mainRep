from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r'dialogs', views.DialogViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'dialogowners', views.DialogOwnersViewSet)

urlpatterns = [
    path('', include(router.urls)),
]