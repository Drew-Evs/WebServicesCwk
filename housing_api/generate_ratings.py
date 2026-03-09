import os
import django
import random

# 1. SETUP DJANGO ENVIRONMENT
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housing_api.settings')
django.setup()

# 2. IMPORT MODELS
from django.db.models import Avg
from django.contrib.auth.models import User
from london_housing.models import Housing, Area, Rating

def generate_bulk_ratings():
    print("--- STARTING RATING GENERATOR ---")
    
    # Grab our mock users and all Kaggle houses
    users = list(User.objects.exclude(is_superuser=True))
    areas = list(Area.objects.all())
    all_houses = list(Housing.objects.all())
    
    if not users or not all_houses:
        print("ERROR: Missing users or houses. Please run your populate.py script first!")
        return
        
    print(f"Found {len(areas)} Areas, {len(all_houses)} Houses, and {len(users)} Users.")
    
    ratings_created = 0

    # --- PHASE 1: GUARANTEE EVERY AREA GETS RATED ---
    print("\nPhase 1: Ensuring every Area has at least one rating...")
    for area in areas:
        # Find all houses that belong strictly to this area
        houses_in_area = Housing.objects.filter(area=area)
        
        if houses_in_area.exists():
            house = random.choice(houses_in_area)
            user = random.choice(users)
            score = random.randint(4, 10) # 4 to 10 for a realistic baseline
            
            # get_or_create prevents crashes if the user already rated this house!
            rating, created = Rating.objects.get_or_create(
                user=user, 
                housing=house,
                defaults={'score': score, 'comments': "Area baseline rating."}
            )
            
            if created:
                ratings_created += 1
        else:
            print(f"  Warning: '{area.name}' has no houses to rate. Skipping.")

    print(f"Phase 1 Complete: {ratings_created} baseline ratings created.")

    # --- PHASE 2: BULK UP TO 1000 RATINGS ---
    target = 1000
    print(f"\nPhase 2: Generating random ratings to hit {target} total...")
    
    # Cap the target just in case there aren't enough unique user/house combinations
    max_possible_ratings = len(users) * len(all_houses)
    actual_target = min(target, max_possible_ratings)

    # Use a while loop to keep trying until we successfully hit our exact target
    attempts = 0
    while ratings_created < actual_target and attempts < 5000:
        attempts += 1
        house = random.choice(all_houses)
        user = random.choice(users)
        score = random.randint(1, 10)
        
        rating, created = Rating.objects.get_or_create(
            user=user, 
            housing=house,
            defaults={'score': score, 'comments': "Randomly generated bulk rating."}
        )
        
        if created:
            ratings_created += 1

    print(f"Phase 2 Complete: Total new ratings created today: {ratings_created}")

# --- PHASE 3: RECALCULATE ALL AVERAGES ---
    print("\nPhase 3: Synchronizing average ratings across the database...")
    
    # 1. Update Houses (FIX: Changed 'rating' to 'ratings' to match your models.py!)
    rated_houses = Housing.objects.filter(ratings__isnull=False).distinct()
    
    for house in rated_houses:
        house_avg = Rating.objects.filter(housing=house).aggregate(Avg('score'))['score__avg']
        house.average_rating = round(house_avg, 2) if house_avg else 0.0
        house.save()
        
    # 2. Update Areas
    for area in areas:
        area_avg = Rating.objects.filter(housing__area=area).aggregate(Avg('score'))['score__avg']
        area.average_rating = round(area_avg, 2) if area_avg else 0.0
        area.save()

    print("--- SUCCESS! ALL AREAS RATED AND AVERAGES CALCULATED ---")

if __name__ == '__main__':
    generate_bulk_ratings()