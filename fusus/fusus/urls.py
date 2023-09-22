from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),  # users 앱의 urls를 api/ 경로에 포함
    # 다른 앱의 urls도 같은 방식으로 포함할 수 있습니다.
]