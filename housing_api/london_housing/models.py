from django.db import models
#using django user model
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

#grouping housing by area and averaging price/rating
class Area(models.Model):
    area_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    #average out the prices and ratings of houses in the area 
    average_price = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    average_rating = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
    
#the housing data imported from the csv
class Housing(models.Model):
    #id and link to an area via foreign key
    housing_id = models.AutoField(primary_key=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='properties')

    #the attributes from the database
    address = models.CharField(max_length=255)
    property_type = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    area_sqft = models.IntegerField(null=True, blank=True)
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    receptions = models.IntegerField()

    def __str__(self):
        return f'{self.address} in {self.area.name}'

#allow 1-1 mapping of users ratings to housing
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    housing = models.ForeignKey(Housing, on_delete=models.CASCADE, related_name='ratings')

    #limit to 1 to 10 ratings
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    comments = models.TextField(blank=True, null=True)

    #want to be able to sort by most recent 
    created_at = models.DateTimeField(auto_now_add=True)

    #want to ensure only 1 rating from each user per house
    class Meta:
        unique_together = ('user', 'housing')

    def __str__(self):
        return f'{self.housing.address} rated: {self.score}/10 by {self.user.username}'