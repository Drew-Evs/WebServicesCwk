import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Housing, Area

#user accounts
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

# Create your views here.

#allows testing POST
@csrf_exempt
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

        #map database to a dictionary
        data = []

        #loop through each house + add to dictionary
        for house in houses:
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
        return JsonResponse({"number of houses": houses.count(), "houses": data}, safe=False, status=200)

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
        
    
