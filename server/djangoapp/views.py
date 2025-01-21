# Uncomment the required imports before adding the code

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate

from .models import CarModel, CarMake
from .restapis import get_request, analyze_review_sentiments, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    data = {"Username": ""}
    return JsonResponse(data)

# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
    context = {}

    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    email_exist = False
    try:
        # Check if user already exists
        User.objects.get(username=username)
        username_exist = True
    except:
        # If not, simply log this is a new user
        logger.debug("{} is new user".format(username))

    # If it is a new user
    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,password=password, email=email)
        # Login the user and redirect to list page
        login(request, user)
        data = {"userName":username,"status":"Authenticated"}
        return JsonResponse(data)
    else :
        data = {"userName":username,"error":"Already Registered"}
        return JsonResponse(data)

def get_cars(request):
    count = CarMake.objects.filter().count()
    print(count)
    if (count == 0):
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({"CarModel": car_model.name, "CarMake": car_model.car_make.name})
    return JsonResponse({"CarModels": cars})

# # Update the `get_dealerships` view to render the index page with
#Update the `get_dealerships` render list of dealerships all by default, particular state if state is passed
import requests
from django.http import JsonResponse

def get_dealerships(request, state="All"):
    api_url = "https://duyphuclengu-3030.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/fetchDealers"
    
    response = requests.get(api_url)
    if response.status_code == 200:
        dealerships = response.json()
        if state != "All":
            dealerships = [d for d in dealerships if d['state'] == state]
        return JsonResponse({"status": 200, "dealers": dealerships})
    else:
        return JsonResponse({"status": response.status_code, "error": "Failed to fetch dealers from API"})


# Create a `get_dealer_reviews` view to render the reviews of a dealer
def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        api_url = f"https://duyphuclengu-3030.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/fetchReviews/dealer/{dealer_id}"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            reviews = response.json()
            for review in reviews:
                sentiment = analyze_review_sentiments(review['review'])
                review['sentiment'] = sentiment['sentiment']
            return JsonResponse({"status": 200, "reviews": reviews})
        except requests.exceptions.RequestException as e:
            return JsonResponse({"status": 500, "message": f"Error: {str(e)}"}, status=500)
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"}, status=400)

# Create a `get_dealer_details` view to render the dealer details
def get_dealer_details(request, dealer_id):
    if dealer_id:
        api_url = f"https://duyphuclengu-3030.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/fetchDealer/{dealer_id}"
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            dealer_data = response.json()
            return JsonResponse({"status": 200, "dealer": dealer_data})
        except requests.exceptions.RequestException as e:
            return JsonResponse({"status": 500, "message": f"Error: {str(e)}"}, status=500)
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"}, status=400)

def add_review(request):
    if(request.user.is_anonymous == False):
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status":200})
        except:
            return JsonResponse({"status":401,"message":"Error in posting review"})
    else:
        return JsonResponse({"status":403,"message":"Unauthorized"})