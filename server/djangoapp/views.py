from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .models import CarModel
from .restapis import get_request, post_review

logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']

    user = authenticate(username=username, password=password)
    data = {"userName": username}

    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}

    return JsonResponse(data)


def logout_request(request):
    logout(request)
    return JsonResponse({"userName": ""})


@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get("userName", "").strip()
        password = data.get("password", "")
        first_name = data.get("firstName", "").strip()
        last_name = data.get("lastName", "").strip()
        email = data.get("email", "").strip()

        if not all([username, password, first_name, last_name, email]):
            return JsonResponse(
                {"error": "All fields are required"}, status=400
            )

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Already Registered"}, status=409)

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        login(request, user)

        return JsonResponse({
            "userName": user.username,
            "status": "Authenticated"
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


def get_cars(request):
    car_models = CarModel.objects.select_related('car_make')
    cars = []

    for car_model in car_models:
        cars.append({
            "CarModel": car_model.name,
            "CarMake": car_model.car_make.name
        })

    return JsonResponse({"CarModels": cars})


def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state

    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_details(request, dealer_id):
    dealer = get_request("/fetchDealer/" + str(dealer_id))
    return JsonResponse({"status": 200, "dealer": dealer})


def get_dealer_reviews(request, dealer_id):
    reviews = get_request("/fetchReviews/dealer/" + str(dealer_id))
    return JsonResponse({"status": 200, "reviews": reviews})


@csrf_exempt
def add_review(request):
    if request.user.is_authenticated:
        if request.method != "POST":
            return JsonResponse(
                {"status": 405, "message": "POST method required"},
                status=405
            )
        try:
            data = json.loads(request.body)
            response = post_review(data)
            if response is not None:
                return JsonResponse({
                    "status": 200,
                    "message": "Review posted successfully"
                })
            return JsonResponse(
                {"status": 401, "message": "Error in posting review"},
                status=401
            )
        except Exception:
            return JsonResponse(
                {"status": 401, "message": "Error in posting review"},
                status=401
            )
    return JsonResponse(
        {"status": 403, "message": "Unauthorized"},
        status=403
    )
