from django.contrib import admin
from django.urls import path, include
from booking.views import index

urlpatterns = [
    path('admin/', admin.site.urls),

    # UI routes (NO prefix)
    path('', include('booking.urls')),

    # API routes (optional future separation)
    # path('api/', include('booking.api_urls')),
]