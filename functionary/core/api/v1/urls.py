from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FunctionViewSet,
    PackageViewSet,
    TaskViewSet,
    TeamViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"functions", FunctionViewSet)
router.register(r"packages", PackageViewSet)
router.register(r"tasks", TaskViewSet)
router.register(r"teams", TeamViewSet)
router.register(r"users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
