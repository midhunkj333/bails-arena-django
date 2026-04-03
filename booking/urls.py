from django.urls import path
from .views import index, get_slots, report, report_view, download_report

urlpatterns = [
    path('', index),
    path('slots/', get_slots),

    # API
    path('api/report/', report),

    # UI
    path('reports/', report_view),
    path('download-report/', download_report),
]