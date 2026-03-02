import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from .models import Housing, Area, Rating, Portfolio

#user accounts
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

#imports to allow rate limitiing
#rate limiting stops oto many records loading at once - prevents crashings
import time
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage

#decorator to limit rates - only a certain amount of requests in the time window
def rate_limit(max_requests=60, window=60):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            #get IP address of the user - use to cache number of requests
            ip = request.META.get('REMOTE_ADDR')
            cache_key = f"rate_limit_{ip}"

            #check number of requests (ensure less than max) - error coede (429)
            requests_made = cache.get(cache_key, 0)
            if requests_made >= max_requests:
                return JsonResponse({"error": "Too many requests made - exceeded API limit"}, status=429)
            
            #increment num of requestws and timeout
            cache.set(cache_key, requests_made+1, timeout=window)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

#allows testing POST
@csrf_exempt
#rate limit the housing - 30 requests a minute
@rate_limit(max_requests=30, window=60)
def housing_list(request):
    #if GET need to read all of the housing listing
    if request.method == 'GET':
        houses = Housing.objects.all()

        #potential filters for the housing
        area_filter = request.GET.get('area')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        min_beds = request.GET.get('bedrooms')
        prop_type = request.GET.get('type')

        #apply filters to the query results
        #filter case insensitive 
        if area_filter:
            houses = houses.filter(area__name__icontains=area_filter)

        #greater or equal to
        if min_price:
            houses = houses.filter(price__gte=min_price)

        #less than or equal to
        if max_price:
            houses = houses.filter(price__lte=max_price)

        if min_beds:
            houses = houses.filter(bedrooms__gte=min_beds)

        if prop_type:
            houses = houses.filter(property_type__icontains=prop_type)

        #include pagination logic - limits to only 20 houses per page
        page_number = request.GET.get('page', 1)
        per_page = request.GET.get('limit', 20)
        paginator = Paginator(houses, per_page)

        #try to get correct page - if still values to get
        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            return JsonResponse({"error": "Page not found - run out of houses"}, status=404)

        #map database to a dictionary
        data = []

        #loop through each house + add to dictionary
        for house in page_obj:
            data.append({
                "id": house.housing_id,
                "address": house.address,
                "property_type": house.property_type,
                "price": float(house.price),
                "bedrooms": house.bedrooms,
                "area_name": house.area.name
            })

        if houses.count() == 0:
            #return HttpResponse(status=204) can use this if correct code wanted but doesnt display anything
            return JsonResponse({"Output": "No houses match", "houses": []}, status=200)

        #return as a Json Response
        return JsonResponse({
            "meta": {
                "total_results": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "has_next_page": page_obj.has_next(),
                "has_previous_page": page_obj.has_previous()
            }, "houses":data
            }, safe=False, status=200)

    #post for creating a new house
    elif request.method == 'POST':
        #parse incoming JSON and check for existing area (may have to create)
        try: 
            body = json.loads(request.body)
            area_name = body.get('area_name', '').strip()
            address = body.get('address', '').strip()

            #validate if containing an address/area name
            #400 code for an invalid request 
            if not address or not area_name:
                return JsonResponse({
                    "error": "Both 'address' and 'area_name' are required fields and cannot be empty."
                }, status=400)
            
            area_obj, created = Area.objects.get_or_create(name=area_name)

            #create new house record
            new_house = Housing.objects.create(
                area=area_obj,
                address=address,
                property_type=body.get('property_type'),
                price=body.get('price'),
                area_sqft=body.get('area_sqft'),
                bedrooms=body.get('bedrooms', 0),
                bathrooms=body.get('bathrooms', 0),
                receptions=body.get('receptions', 0),
                for_sale=body.get('for_sale', False),
                for_rent=body.get('for_rent', False)
            )

            return JsonResponse({"message": "House Created", "id":new_house.housing_id}, status=201)
        
        #see if Json was coded incorrectly
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format provided."}, status=400)
        
        #outputs the exception if the creation fails
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


#register route
@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        #get the account details entered and push to database
        try:
            body = json.loads(request.body)
            username = body.get('username', '').strip()
            password = body.get('password', '').strip()
            email = body.get('email', '').strip()

            #need to ensure that username and password are not empty and dont already exist
            if not username or not password:
                return JsonResponse({"error": "Username and Password are required"}, status=400)
            #409 shows a conflict
            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "This Username is already taken"}, status=409)
            
            user = User.objects.create_user(username=username, email=email, password=password)

            return JsonResponse({"message": f"Account created for {user.username}"}, status=201)
        
        #if theres a server error/unkown method
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
#login route
@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            #get the login details
            body = json.loads(request.body)
            username = body.get('username', '').strip()
            password = body.get('password', '').strip()

            #authenticate the user by checking the database with the username and hashed password
            user = authenticate(username=username, password=password)

            #ensures user exists
            if user is not None:
                login(request, user)
                return JsonResponse({"message": f"{user.username} is logged in"}, status=200)
            
            #if not need a 401 unauthorised user
            else:
                return JsonResponse({"error": "Invalid Username or Password"}, status=401)
            
        #if theres a server error/unkown method
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
#logout route
@csrf_exempt
def logout_user(request):
    if request.method == 'POST':
        try:
            #security needs to check login in - otherwise unauthorised
            if not request.user.is_authenticated:
                return JsonResponse({
                    "error": "Unauthorized. You must be logged in to log out."
                }, status=401)

            #then allow logout
            logout(request)
            return JsonResponse({"message": "Successfully"}, status=200)
            
        #if theres a server error/unkown method
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    #need to use the correct method 405 = incorrect method
    else:
        return JsonResponse({"error": "Method not allowed - use POST"}, status=405)
        
    
@csrf_exempt
def rate_house(request):
    #post for creating a new rating
    if request.method == 'POST':
        #test user logged in
        if not request.user.is_authenticated:
            return JsonResponse({"error": "User must be logged in to rate"}, status=401)
        
        #get the info - body may be blank
        try:
            body = json.loads(request.body)
            address = body.get('address')
            score = body.get('score')
            comments = body.get('comments', '')

            #validate that the required fields are there and that score is between 1 and 10
            if not address or not score:
                return JsonResponse({"error": "'address' and 'score' are required."}, status=400)
            if not (1 <= int(score) <= 10):
                return JsonResponse({"error": "Score must be between 1 and 10."}, status=400)
            
            #handle missing house error (404 - not found)
            try:
                house = Housing.objects.get(address=address)
            except Housing.DoesNotExist:
                return JsonResponse({"error": f"House with this ID doesn't exist"}, status = 404)
            
            #create/update rating - if already exists (must be unique)
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                housing=house,
                defaults={'score': score, 'comments': comments}
            )

            #update the average score for the house
            house_avg = Rating.objects.filter(housing=house).aggregate(Avg('score'))['score__avg']
            house.average_rating = house_avg
            house.save()

            #and fo rthe area
            area = house.area
            area_avg = Rating.objects.filter(housing__area=area).aggregate(Avg('score'))['score__avg']
            area.average_rating = area_avg
            area.save()

            #return if successful
            return JsonResponse({
                "message": "Rating submitted successfully!",
                "house_address": house.address,
                "new_house_average": round(house_avg, 2),
                "new_area_average": round(area_avg, 2)
            }, status=200)

        #server error
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    #the delete method to get rid of a rating they have made
    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return JsonResponse({"error": "User must be logged in to delete a rating"}, status=401)
        
        try:
            body = json.loads(request.body)
            address = body.get('address', '').strip()

            #if the address doesnt exist return error
            if not address:
                return JsonResponse({"error": "Need to enter 'address' to delete"}, status=400)
            
            #get the house and check the user owns it
            try:
                rating = Rating.objects.get(user=request.user, housing=house)
                rating.delete()
            except Rating.DoesNotExist:
                return JsonResponse({"error": "You have not rated this house"}, status=404)

            #recalculate averages and set to 0 if no items left
            house_avg = Rating.objects.filter(housing=house).aggregate(Avg('score'))['score__avg']
            house.average_rating = house_avg if house_avg is not None else 0
            house.save()

            area = house.area
            area_avg = Rating.objects.filter(housing__area=area).aggregate(Avg('score'))['score__avg']
            area.average_rating = area_avg if area_avg is not None else 0
            area.save()

            return JsonResponse({
                "message": "Rating deleted successfully.",
                "new_house_average": round(house.average_rating, 2),
                "new_area_average": round(area.average_rating, 2)
            }, status=200)
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    #incorrect method
    else:
        return JsonResponse({"error": "Method not allowed. Use POST/DELTETE."}, status=405)
    

#method to allow user portfolio
@csrf_exempt
def user_portfolio(request):
    #need to be logged in to view/add to porfolio - if not error 401
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorised - login first"}, status=401)
    
    #GET - view portfolio
    if request.method == 'GET':
        try:
            #fetch portfolio items from user
            portfolio_items = Portfolio.objects.filter(user=request.user)

            data = []
            for item in portfolio_items:
                data.append({
                    "portfolio_id": item.id,
                    "house_id": item.housing.housing_id,
                    "address": item.housing.address,
                    "area": item.housing.area.name,
                    "status": item.get_status_display(),
                    "rent_pcm": float(item.rent_pcm) if item.rent_pcm else None,
                    "added_on": item.added_on.strftime("%Y-%m-%d %H:%M")
                })

            return JsonResponse({"my_porfolio": data, "total_properties": portfolio_items.count()}, status=200)

        #except server error - code 500
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    #else want to add house to the porfolio
    elif request.method == 'POST':
        try:
            #attempt to connect to a house in the database
            body = json.loads(request.body)
            create_filter = str(body.get('create'))
            address = body.get('address', '').strip()

            #decide if needs to create or link 
            if create_filter == 'True':
                #needs addresss and area name
                area = body.get('area_name', '').strip()

                if not address or not area:
                    return JsonResponse({"error": "Needs either an 'address' and 'area_name"}, status=400)
                
                area_obj, _ = Area.objects.get_or_create(name=area)

                #create new house
                house = Housing.objects.create(
                    area=area_obj,
                    address=address,
                    property_type=body.get('property_type', 'Unknown'),
                    price=body.get('price', 0),
                    bedrooms=body.get('bedrooms', 0),
                    bathrooms=body.get('bathrooms', 0),
                    receptions=body.get('receptions', 0),
                    for_sale=body.get('for_sale', False),
                    for_rent=body.get('for_rent', False)
                )

            elif create_filter == 'False':
                #test if house exists - error 404 if not
                try:
                    house = Housing.objects.get(address=address)
                except Housing.DoesNotExist:
                    return JsonResponse({"error": f"House with address: {address} not found"}, status=404)

                #check for conflict - house already registered to other users portfolio (conflict = 409)
                if Portfolio.objects.filter(housing=house).exclude(user=request.user).exists():
                    return JsonResponse({"error": "Conflict as house is already registered to another user"}, status=409)

            #else invalid needs create_filter
            else:
                return JsonResponse({"error": "Requires 'create_filter'"}, status=400)

            #then link to the portfolio table
            status = body.get('status', 'LIVING')
            rent_pcm = body.get('rent_pcm', None)

            #update or create stops a user creating the same house twice
            portfolio_entry, created = Portfolio.objects.update_or_create(
                user=request.user,
                housing=house,
                defaults={
                    'status': status,
                    'rent_pcm': rent_pcm
                }
            )

            msg = "House added to portfolio" if created else "Portfolio entry updated"

            #return success message
            return JsonResponse({
                "message": msg,
                "portfolio_id": portfolio_entry.id,
                "house_address": house.address,
                "status": portfolio_entry.get_status_display()
            }, status=202 if create_filter == 'True' else 200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
                  
    #the PUT method to update
    elif request.method == 'PUT':
        try:
            body = json.loads(request.body)
            address = body.get('address', '').strip()

            #if the address doesnt exist return error
            if not address:
                return JsonResponse({"error": "Need to enter 'address' to update"}, status=400)
            
            #get the house and check the user owns it
            try:
                house = Housing.objects.get(address=address)
            except Housing.DoesNotExist:
                return JsonResponse({"error": "House not found"}, status=404)
            #using status 403 for forbidden (does not own)
            try:
                portfolio_entry = Portfolio.objects.get(user=request.user, housing=house)
            except Portfolio.DoesNotExist:
                return JsonResponse({"error": "Forbidden: do not own property"}, status=403)
            
            #update property if data given - if not default to old value
            house.property_type = body.get('property_type', house.property_type)
            house.price = body.get('price', house.price)
            house.bedrooms = body.get('bedrooms', house.bedrooms)
            house.bathrooms = body.get('bathrooms', house.bathrooms)
            house.receptions = body.get('receptions', house.receptions)
            house.for_sale = body.get('for_sale', house.for_sale)
            house.for_rent = body.get('for_rent', house.for_rent)
            house.save()

            #update portfolio in same way
            portfolio_entry.status = body.get('status', portfolio_entry.status)
            portfolio_entry.rent_pcm = body.get('rent_pcm', portfolio_entry.rent_pcm)
            portfolio_entry.save()

            return JsonResponse({"message": "Property updated successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    #the delete method to get rid of a house they own
    elif request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            address = body.get('address', '').strip()

            #if the address doesnt exist return error
            if not address:
                return JsonResponse({"error": "Need to enter 'address' to delete"}, status=400)
            
            #get the house and check the user owns it
            try:
                house = Housing.objects.get(address=address)
            except Housing.DoesNotExist:
                return JsonResponse({"error": "House not found"}, status=404)
            #using status 403 for forbidden (does not own)
            try:
                portfolio_entry = Portfolio.objects.get(user=request.user, housing=house)
            except Portfolio.DoesNotExist:
                return JsonResponse({"error": "Forbidden: do not own property"}, status=403)
            
            #then delete - will cascade to delete portfolio
            house.delete()

            return JsonResponse({"message": f"Property {address} deleted successfully"}, status=200)
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    #if not need to return an error
    else:
        return JsonResponse({"error": "Need to use PUT, DELETE, POST or GET"}, status=405)
            
            