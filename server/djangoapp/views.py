# Uncomment the required imports before adding the code

# from django.shortcuts import render
# from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
# from django.shortcuts import get_object_or_404, render, redirect
# from django.contrib.auth import logout
# from django.contrib import messages
# from datetime import datetime

from django.http import JsonResponse
import logging
import json
from django.views.decorators.csrf import csrf_exempt
# from .populate import initiate
from django.contrib.auth import authenticate, login, logout
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
    data = {"userName": ""}
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
        User.objects.get(username=username)
        username_exist = True
    except BaseException:
        logger.debug("{} is new user".format(username))

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email)
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(data)
    else:
        data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(data)

# Update the `get_dealerships` to render list of dealerships all by
# default, or particular state if state is passed


def get_dealerships(request, state="All"):
    if (state == "All"):
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})

# Create get_dealer_details method which takes the dealer_id as a parameter


def get_dealer_details(request, dealer_id):
    if (dealer_id):
        endpoint = "/fetchDealer/" + str(dealer_id)
        dealership = get_request(endpoint)
        return JsonResponse({"status": 200, "dealer": dealership})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})

# Create get_dealer_reviews method which takes the dealer_id as a
# parameter and adds sentiment analysis


def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        reviews = get_request(endpoint)

        # Guard against backend returning an error object instead of a list
        if not isinstance(reviews, list):
            return JsonResponse({"status": 500,
                                 "message": "Invalid response from backend service",
                                 "details": reviews})

        for review_detail in reviews:
            try:
                # Ensure 'review' key exists and is not empty
                review_text = review_detail.get('review', '')
                if review_text:
                    sentiment_response = analyze_review_sentiments(review_text)
                    # Safely grab sentiment, fallback to 'neutral' if missing
                    review_detail['sentiment'] = sentiment_response.get(
                        'sentiment', 'neutral')
                else:
                    review_detail['sentiment'] = 'neutral'
            except Exception as e:
                print(f"Error analyzing sentiment for review: {e}")
                # Fallback so the loop doesn't crash
                review_detail['sentiment'] = 'neutral'

        return JsonResponse({"status": 200, "reviews": reviews})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


# Create a `add_review` view to submit a review
def add_review(request):
    if (request.user.is_anonymous == False):
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status": 200})
        except BaseException:
            return JsonResponse(
                {"status": 401, "message": "Error in posting review"})
    else:
        return JsonResponse({"status": 403, "message": "Unauthorized"})
        # ...


def get_cars(request):
    try:
        # Calls your Node server endpoint (e.g.,
        # http://localhost:3030/get_cars)
        cars = get_request("/get_cars")
        if cars:
            return JsonResponse(cars)
        return JsonResponse({"CarModels": []})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
