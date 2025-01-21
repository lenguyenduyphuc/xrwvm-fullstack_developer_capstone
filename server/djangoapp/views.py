from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging
import requests
from .models import CarModel, CarMake
from .populate import initiate

logger = logging.getLogger(__name__)

from .models import CarModel, CarMake
from .restapis import get_request, analyze_review_sentiments, post_review

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
    if CarMake.objects.count() == 0:
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = [{"CarModel": car.name, "CarMake": car.car_make.name} for car in car_models]
    return JsonResponse({"CarModels": cars})

def get_dealerships(request, state="All"):
    endpoint = "/fetchDealers"
    try:
        dealerships = get_request(endpoint)
        if state != "All":
            dealerships = [d for d in dealerships if d['state'] == state]
        return JsonResponse({"status": 200, "dealers": dealerships})
    except Exception as e:
        return JsonResponse({"status": 500, "error": str(e)}, status=500)

def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = f"https://duyphuclengu-3030.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/fetchDealer/{dealer_id}"
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                dealership = response.json()
                return JsonResponse({"status": 200, "dealer": [dealership]})  # Wrap dealership in a list
            else:
                return JsonResponse({"status": response.status_code, "error": "Failed to fetch dealer details"}, status=400)
        except Exception as e:
            return JsonResponse({"status": 500, "error": str(e)}, status=500)
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"}, status=400)

def get_dealer_reviews(request, dealer_id):
    endpoint = f"/fetchReviews/dealer/{dealer_id}"
    try:
        # Add some debug logging
        print(f"Fetching reviews for dealer {dealer_id}")
        reviews = get_request(endpoint)
        
        # Add error checking for empty reviews
        if not reviews:
            return JsonResponse({"status": 404, "message": "No reviews found"})
            
        # Add try-catch for sentiment analysis
        for review in reviews:
            try:
                sentiment = analyze_review_sentiments(review['review'])
                review['sentiment'] = sentiment['sentiment']
            except Exception as e:
                review['sentiment'] = 'neutral'
                print(f"Sentiment analysis failed: {str(e)}")
                
        return JsonResponse({"status": 200, "reviews": reviews})
    except Exception as e:
        print(f"Error fetching reviews: {str(e)}")  # Add debug logging
        return JsonResponse({"status": 500, "error": str(e)}, status=500)

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