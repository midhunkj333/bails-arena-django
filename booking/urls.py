from django.urls import path
from .views import login_view,logout_view, index, get_slots, report, report_view, download_report

urlpatterns = [
    path('', index),

    # API
    path('api/slots/', get_slots),   # 👈 FIXED
    path('api/report/', report),

    # UI
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('reports/', report_view),
    path('download-report/', download_report),
]