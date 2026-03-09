'''script to populate the tables rent/user/portfolio tables'''
import os
import django
import random
from decimal import Decimal

# 1. SETUP DJANGO ENVIRONMENT
# Change 'housing_api.settings' if your main project folder has a different name!
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_api.settings')
django.setup()

# 2. IMPORT MODELS
from django.contrib.auth.models import User
from london_housing.models import Housing, Area, Rating, Portfolio, Rent
from django.db.models import Avg, Count

def populate_database():
    with open('populated_data.txt', 'w', encoding='utf-8') as log_file:
        def log(msg):
            print(msg)
            log_file.write(msg + '\n')

        log("--- STARTING DATABASE POPULATION ---")

        log("Clearing old data...")
        User.objects.exclude(is_superuser=True).delete()
        Area.objects.all().delete()
        
        # 1. CREATE AREAS
        area_names = ["Camden", "Hackney", "Chelsea", "Islington", "Greenwich"]
        areas = []
        for name in area_names:
            area, _ = Area.objects.get_or_create(name=name)
            areas.append(area)
        log(f"Created {len(areas)} Areas.")

        # 2. CREATE USERS
        users = []
        log("\n--- CREATING 30 USERS ---")
        for i in range(1, 31):
            username = f"user_{i}"
            email = f"{username}@test.com"
            user = User.objects.create_user(username=username, email=email, password="password123")
            users.append(user)
            log(f"User: {username} | Pass: password123")

        # 3. CREATE HOUSING & PORTFOLIOS
        houses = []
        property_types = ["Flat", "Detached", "Semi-Detached", "Terraced", "Mansion"]
        
        log("\n--- CREATING HOUSING & ASSIGNING PORTFOLIOS ---")
        for i in range(1, 61):  
            area = random.choice(areas)
            prop_type = random.choice(property_types)
            address = f"{i} {random.choice(['High St', 'Station Rd', 'Church Ln', 'Park Ave'])}"
            price = random.randint(200000, 1500000)
            
            for_sale = random.choice([True, False])
            for_rent = random.choice([True, False]) if not for_sale else False

            house = Housing.objects.create(
                area=area,
                address=address,
                property_type=prop_type,
                price=price,
                bedrooms=random.randint(1, 5),
                bathrooms=random.randint(1, 3),
                for_sale=for_sale,
                for_rent=for_rent
            )
            houses.append(house)

            # Assign to the Landlord's portfolio
            owner = random.choice(users)
            status = 'LIVING' if not for_rent else 'RENTING_OUT'
            Portfolio.objects.create(user=owner, housing=house, status=status)
            
            log(f"House: {address} ({area.name}) - £{price} | Market: Sale={for_sale}, Rent={for_rent} | Owner: {owner.username}")

        # 4. CREATE RATINGS
        log("\n--- GENERATING RATINGS ---")
        for user in users:
            houses_to_rate = random.sample(houses, random.randint(2, 4))
            for house in houses_to_rate:
                score = random.randint(5, 10) 
                Rating.objects.create(user=user, housing=house, score=score, comments="Automated test rating.")
                log(f"Rating: {user.username} rated {house.address} a {score}/10")

                house_avg = Rating.objects.filter(housing=house).aggregate(Avg('score'))['score__avg']
                house.average_rating = house_avg
                house.save()

        for area in areas:
            area_avg = Rating.objects.filter(housing__area=area).aggregate(Avg('score'))['score__avg']
            area.average_rating = area_avg if area_avg else 0
            area.save()

        # 5. CREATE TENANCIES (RENT)
        log("\n--- GENERATING TENANCIES ---")
        rentable_houses = [h for h in houses if h.for_rent]
        
        # Keep track of users who are already renting so they don't rent twice
        active_tenants = set()
        
        for house in random.sample(rentable_houses, min(10, len(rentable_houses))):
            # Grab the Landlord's portfolio entry FIRST
            landlord_portfolio = Portfolio.objects.get(housing=house)
            landlord = landlord_portfolio.user
            
            # Find eligible tenants: Must NOT be the landlord, and NOT already renting somewhere else
            eligible_tenants = [u for u in users if u != landlord and u not in active_tenants]
            
            if not eligible_tenants:
                log("Ran out of eligible tenants!")
                break
                
            tenant = random.choice(eligible_tenants)
            active_tenants.add(tenant) # Mark them as currently renting
            
            rent_pcm = round(Decimal(random.randint(800, 3500)), 2)
            
            # Link the Rent agreement to the Portfolio entry
            Rent.objects.create(
                housing=landlord_portfolio, 
                tenant=tenant,
                actual_rent_pcm=rent_pcm, # Note: if your model uses rent_pcm instead of actual_rent_pcm, update this!
                active=True
            )
            
            # Create a separate portfolio entry for the tenant to show they live there
            Portfolio.objects.create(user=tenant, housing=house, status='RENTING', rent_pcm=rent_pcm)
            
            # Take off market
            house.for_rent = False
            house.save()
            log(f"Tenancy: {tenant.username} is renting {house.address} from {landlord.username} for £{rent_pcm}/mo")

        log("\n--- POPULATION COMPLETE! ---")

if __name__ == '__main__':
    print("Populating database... this might take a few seconds.")
    populate_database()
    print("Done! Check 'populated_data.txt' for the full output.")