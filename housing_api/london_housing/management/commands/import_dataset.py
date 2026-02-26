import os 
import csv
import kagglehub
from django.core.management.base import BaseCommand
from london_housing.models import Area, Housing

class Command(BaseCommand):
    help = 'Downloads housing data from kaggle then import to database'

    def handle(self, *args, **kwargs):
        self.stdout.write("Downloading dataset...")

        # Download latest version of housing csv
        path = kagglehub.dataset_download("arnavkulkarni/housing-prices-in-london")
        csv_file_path = os.path.join(path, "London.csv")

        self.stdout.write(f'Dataset downloaded to {csv_file_path}')
        self.stdout.write('Then importign to the dataset')

        #record number of records added or skipped (skip if dont have location attribute)
        records_added = 0
        records_skipped = 0

        #open then read the csv
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                #drop rows without location
                location_name = row.get('Location', '').strip()
                if not location_name or location_name.lower() == 'none':
                    records_skipped += 1
                    continue

                #check if area exists in the table and if not create new one
                area_obj, created = Area.objects.get_or_create(name=location_name)

                #clean data removing nones and commas - also ensure digits
                try:
                    #ensure floats
                    price = float(row['Price'].replace(',', '')) if row['Price'] else 0 

                    #handles 'none' square footage
                    sqft_raw = row.get('Area in sq ft', '')
                    area_sqft = int(sqft_raw.replace(',', '')) if sqft_raw.isdigit() else None

                    #ensures int fields are integers
                    bedrooms = int(row['No. of Bedrooms']) if row['No. of Bedrooms'].isdigit() else 0
                    bathrooms = int(row['No. of Bathrooms']) if row['No. of Bathrooms'].isdigit() else 0
                    receptions = int(row['No. of Receptions']) if row['No. of Receptions'].isdigit() else 0

                    #create housing record/link it to the area
                    Housing.objects.create(
                        area=area_obj,
                        address=row.get('Property Name', 'Unknown Address'),
                        property_type=row.get('House Type', 'Unknown'),
                        price=price,
                        area_sqft=area_sqft,
                        bedrooms=bedrooms,
                        bathrooms=bathrooms,
                        receptions=receptions
                    )
                    records_added += 1

                #will skip if corrupted data
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Skipped a row due to error: {e}"))
                    records_skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import complete added {records_added} houses and skipped {records_skipped}"
        ))