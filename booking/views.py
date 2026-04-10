from django.shortcuts import render
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Slot, Booking
from datetime import datetime
import csv

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import logout

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "login.html", {
                "error": "Invalid credentials",
                "hide_menu": True
            })

    return render(request, "login.html", {"hide_menu": True})



def logout_view(request):
    logout(request)
    return redirect('/login/')

# ---------------- HOME ----------------
@login_required
def index(request):
    return render(request, "index.html")


# ---------------- SLOT API ----------------
@login_required
def get_slots(request):
    date = request.GET.get('date')

    if not date:
        return JsonResponse({"error": "date is required"}, status=400)

    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    slots = Slot.objects.all()
    data = []

    for slot in slots:
        booking = Booking.objects.filter(date=date_obj, slot=slot).first()

        if booking:
            status = "frequent" if booking.customer.is_frequent else "booked"
            name = booking.customer.name
        else:
            status = "available"
            name = ""

        data.append({
            "slot": str(slot),
            "status": status,
            "customer": name
        })

    return JsonResponse(data, safe=False)


# ---------------- REPORT API ----------------
@login_required
def report(request):
    start = request.GET.get('from')
    end = request.GET.get('to')

    bookings = Booking.objects.filter(date__range=[start, end])

    total = bookings.count()
    revenue = bookings.aggregate(Sum('amount'))['amount__sum'] or 0

    return JsonResponse({
        "total_bookings": total,
        "total_revenue": revenue
    })


# ---------------- REPORT PAGE ----------------
@login_required
def report_view(request):
    start = request.GET.get('from')
    end = request.GET.get('to')

    bookings = []
    total = 0
    revenue = 0

    if start and end:
        bookings = Booking.objects.filter(date__range=[start, end])
        total = bookings.count()
        revenue = bookings.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, "report.html", {
        "bookings": bookings,
        "total": total,
        "revenue": revenue,
        "start": start,
        "end": end
    })


# ---------------- DOWNLOAD CSV ----------------
@login_required
def download_report(request):
    start = request.GET.get('from')
    end = request.GET.get('to')

    bookings = Booking.objects.filter(date__range=[start, end])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bails_arena_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Slot', 'Customer', 'Amount'])

    for b in bookings:
        writer.writerow([b.date, b.slot, b.customer.name, b.amount])

    return response