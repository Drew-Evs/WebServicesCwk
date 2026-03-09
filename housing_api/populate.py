import os
import django
import random
from decimal import Decimal

# 1. SETUP DJANGO ENVIRONMENT
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_api.settings')
django.setup()

# 2. IMPORT MODELS
from django.db.models import Avg
from django.contrib.auth.models import User
from london_housing.models import Housing, Area, Rating, Portfolio, Rent

def populate_database():
    with open('populated_data.txt', 'w', encoding='utf-8') as log_file:
        def log(msg):
            print(msg)
            log_file.write(msg + '\n')

        log("--- STARTING NON-DESTRUCTIVE POPULATION ---")

        log("Clearing old test users, portfolios, and tenancies...")
        User.objects.exclude(is_superuser=True).delete()
        
        all_houses = list(Housing.objects.all())
        
        if not all_houses:
            log("ERROR: No houses found! Please run your Kaggle import script first.")
            return

        log(f"Successfully found {len(all_houses)} existing houses from your Kaggle import.")

        # 1. CREATE USERS
        users = []
        log("\n--- CREATING 30 USERS ---")
        for i in range(1, 31):
            username = f"user_{i}"
            user = User.objects.create_user(username=username, email=f"{username}@test.com", password="password123")
            users.append(user)

        # 2. ASSIGN REAL HOUSES TO PORTFOLIOS
        log("\n--- ASSIGNING 200 RANDOM LONDON HOUSES TO USERS ---")
        test_houses = random.sample(all_houses, min(200, len(all_houses)))
        
        # We will keep a list of portfolios that are actively looking for renters
        rentable_portfolios = []

        for house in test_houses:
            owner = random.choice(users)
            
            for_sale = random.choice([True, False])
            for_rent = random.choice([True, False]) if not for_sale else False
            
            house.for_sale = for_sale
            house.for_rent = for_rent
            house.save()

            # Set initial status based on market flags
            if for_sale:
                status = 'SELLING'
            elif for_rent:
                status = 'RENTING'
            else:
                status = 'LIVING'
                
            # EVERY portfolio item gets a rent_pcm, as requested!
            base_rent = round(Decimal(random.randint(800, 3500)), 2)

            portfolio_item = Portfolio.objects.create(
                user=owner, 
                housing=house, 
                status=status,
                rent_pcm=base_rent
            )
            
            if status == 'RENTING':
                rentable_portfolios.append(portfolio_item)
            
        log(f"Assigned {len(test_houses)} real houses to user portfolios.")

        # 3. CREATE RATINGS
        log("\n--- GENERATING RATINGS ---")
        for user in users:
            houses_to_rate = random.sample(test_houses, random.randint(2, 5))
            for house in houses_to_rate:
                score = random.randint(5, 10) 
                Rating.objects.create(user=user, housing=house, score=score, comments="Great Kaggle property!")

                house_avg = Rating.objects.filter(housing=house).aggregate(Avg('score'))['score__avg']
                house.average_rating = house_avg
                house.save()

        # 4. CREATE TENANCIES (RENT)
        log("\n--- GENERATING TENANCIES ---")
        
        # Keep track of active tenants so nobody rents more than one house
        active_tenants = set()
        
        # Try to rent out up to 15 of the available rental portfolios
        for portfolio in random.sample(rentable_portfolios, min(15, len(rentable_portfolios))):
            landlord = portfolio.user
            house = portfolio.housing
            
            # Find a tenant who isn't the landlord, and isn't already renting elsewhere
            eligible_tenants = [u for u in users if u != landlord and u not in active_tenants]
            if not eligible_tenants:
                break # We ran out of free users!
                
            tenant = random.choice(eligible_tenants)
            active_tenants.add(tenant) 
            
            # 1. Create the official Rent link (pointing at the Portfolio item)
            Rent.objects.create(
                housing=portfolio, 
                tenant=tenant,
                actual_rent_pcm=portfolio.rent_pcm,
                active=True
            )
            
            # 2. Update the Landlord's portfolio to show they now have an active tenant
            # (Using your exact spelling from models.py to prevent crashes!)
            portfolio.status = 'ACIVE_TENANT'
            portfolio.save()
            
            # 3. Take the physical house off the rental market
            house.for_rent = False
            house.save()
            
            log(f"Tenancy: {tenant.username} is renting from {landlord.username} for £{portfolio.rent_pcm}/mo")

        # 5. CALCULATE ALL AREA AVERAGES (PRICE & RATING)
        log("\n--- CALCULATING GLOBAL AREA STATISTICS ---")
        areas = Area.objects.annotate(calculated_avg_price=Avg('properties__price'))
        
        for area in areas:
            area.average_price = round(area.calculated_avg_price, 2) if area.calculated_avg_price else 0.0
            
            area_avg_rating = Rating.objects.filter(housing__area=area).aggregate(Avg('score'))['score__avg']
            area.average_rating = round(area_avg_rating, 2) if area_avg_rating else 0.0
            
            area.save()
            
        log(f"Successfully calculated averages for {areas.count()} Areas.")

        log("\n--- POPULATION COMPLETE! ---")

if __name__ == '__main__':
    print("Layering mock data over Kaggle dataset and calculating analytics...")
    populate_database()
    print("Done! Check 'populated_data.txt'.")