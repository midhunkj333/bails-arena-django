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
import json
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Slot, Booking, Customer, Turf, BookingGroup
from django.db import IntegrityError

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

@login_required
def booking_page(request):
    date = request.GET.get('date')
    slot = request.GET.get('slot')

    return render(request, "booking.html", {
        "date": date,
        "slot": slot
    })



@login_required
@csrf_exempt
def customers(request):
    if request.method == "GET":
        data = list(Customer.objects.values("id", "name"))
        return JsonResponse(data, safe=False)

    if request.method == "POST":
        body = json.loads(request.body)

        try:
            customer = Customer.objects.create(
                name=body.get("name"),
                phone=body.get("phone"),
                is_frequent=body.get("is_frequent", False)
            )

            return JsonResponse({
                "id": customer.id,
                "name": customer.name
            })

        except IntegrityError:
            return JsonResponse({
                "error": "Mobile number already exists"
            }, status=400)

@login_required
@csrf_exempt
def book_slot(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    body = json.loads(request.body)

    customer_id = body.get("customer")
    date = body.get("date")
    slots = body.get("slots", [])
    repeat = body.get("repeat")
    repeat_type = body.get("repeatType")
    end_date = body.get("endDate")
    amount = body.get("amount")

    # ✅ validations
    if not amount:
        return JsonResponse({"error": "Amount is required"}, status=400)

    if not customer_id or not date or not slots:
        return JsonResponse({"error": "Missing fields"}, status=400)

    customer = Customer.objects.get(id=customer_id)
    turf = Turf.objects.first()

    base_date = datetime.strptime(date, "%Y-%m-%d").date()

    # 🔁 Generate booking dates
    dates = [base_date]

    if repeat and end_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        step = timedelta(days=1 if repeat_type == "daily" else 7)

        temp = base_date
        while True:
            temp += step
            if temp > end_date_obj:
                break
            dates.append(temp)

    # ✅ Track results
    conflicts = []
    created = []

    try:
        with transaction.atomic():

            # 🆕 create booking group
            group = BookingGroup.objects.create(
                customer=customer,
                turf=turf,
                repeat_type=repeat_type.upper() if repeat else "NONE",
                start_date=base_date,
                end_date=end_date if repeat else None
            )

            for d in dates:
                for slot_str in slots:

                    start, end = slot_str.split(" - ")

                    start_time = datetime.strptime(start.strip(), "%H:%M:%S").time()
                    end_time = datetime.strptime(end.strip(), "%H:%M:%S").time()

                    slot_obj = Slot.objects.filter(
                        start_time=start_time,
                        end_time=end_time
                    ).first()

                    if not slot_obj:
                        conflicts.append(f"Slot not found: {slot_str}")
                        continue

                    # 🚫 check existing booking
                    exists = Booking.objects.filter(
                        date=d,
                        slot=slot_obj,
                        turf=turf
                    ).exists()

                    if exists:
                        conflicts.append(f"{d} {slot_str}")
                        continue

                    # ✅ create booking
                    booking = Booking.objects.create(
                        date=d,
                        slot=slot_obj,
                        turf=turf,
                        customer=customer,
                        amount=amount,
                        group=group,
                        status='BOOKED'
                    )

                    created.append(str(booking.id))

        return JsonResponse({
            "created_count": len(created),
            "conflicts_count": len(conflicts),
            "created": created,
            "conflicts": conflicts,
            "message": f"{len(created)} bookings created successfully"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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