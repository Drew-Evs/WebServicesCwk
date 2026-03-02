from django.core.management.base import BaseCommand
from london_housing.models import Housing
import random

class Command(BaseCommand):
    help = 'Assigns random door numbers to properties that only have a street name'

    def handle(self, *args, **kwargs):
        houses = Housing.objects.all()
        updated_count = 0
        
        for house in houses:
            # THE FIX: We first check if house.address actually exists and isn't empty, 
            # THEN we check if it starts with a digit.
            if house.address and not house.address[0].isdigit(): 
                random_number = random.randint(1, 150)
                house.address = f"{random_number} {house.address}"
                house.save()
                updated_count += 1
                
        # This prints a nice green success message in your terminal when it finishes
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} addresses!'))