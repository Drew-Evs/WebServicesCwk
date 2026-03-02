import json
from django.test import TestCase, Client
from django.contrib.auth.models import User 
from .models import Housing, Area, Portfolio, Rating

#regression test suite for each of the api endpoints

#housing tests
class HousingAPITests(TestCase):
    #run before test to set up a temp ghost database to work with
    def setUp(self):
        self.client = Client()

        #create test area and house
        self.area = Area.objects.create(name="Test Area")
        self.house = Housing.objects.create(
            area=self.area,
            address="123 Fake Street",
            property_type="Detached",
            price=50000,
            bedrooms=2,
            bathrooms=1
        )

    #TEST 1 - GET request - test API returns housing correctly
    def test_get_housing(self):
        #simulate GET request
        response = self.client.get('/api/housing/')

        #check status code
        self.assertEqual(response.status_code, 200)

        #check JSON contains simulated house
        response_data = json.loads(response.content)
        self.assertEqual(response_data["meta"]["total_results"], 1)
        self.assertEqual(response_data["houses"][0]["address"], "123 Fake Street")

    #TEST 2 - POST request - test saves to DB correctly
    def test_new_housing(self):
        #new payload to send
        payload = {
            "area_name": "New Test Area",
            "address": "99 Automated Ave",
            "property_type": "Flat",
            "price": 250000,
            "bedrooms": 2,
            "bathrooms": 1
        }

        #simulate POST request
        response = self.client.post(
            '/api/housing/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        #checks status code is 201 (created)
        self.assertEqual(response.status_code, 201)

        #query database to ensure that the new house exists and area auto created
        house_exists = Housing.objects.filter(address="99 Automated Ave").exists()
        self.assertTrue(house_exists, "Database didn't update with new house")
        area_exists = Area.objects.filter(name="New Test Area").exists()
        self.assertTrue(area_exists, "Database didn't update with new area")

#authentication tests
class AuthAPITests(TestCase):
    #create a test user
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@testmail.com", password="password123")

    #TEST 1 - registering a username - 201 created code
    def test_register_user(self):
        payload = {"username": "newuser", "password": "securepwd", "email": "new@test.com"}
        response = self.client.post('/api/register/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    #TEST 2 - duplicate user should fail - 409 conflict code
    def test_duplicate_user(self):
        payload = {"username": "testuser", "password": "password123", "email": "test@testmail.com"}
        response = self.client.post('/api/register/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 409)
    
    #TEST 3 - ability to login - 200 success code
    def test_login_user(self):
        payload = {"username": "testuser", "password": "password123"}
        response = self.client.post('/api/login/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

#portfolio tests
class PortfolioAPITests(TestCase):
    def setUp(self):
        #create a user and log them in 
        self.client = Client()
        self.user = User.objects.create_user(username="portfolio_owner", password="password123", email="port@testmail.com")
        payload = {"username": "portfolio_owner", "password": "password123"}
        self.client.post('/api/login/', data=json.dumps(payload), content_type='application/json')

        #dummy house/area data
        self.area = Area.objects.create(name="Chelsea")
        self.house = Housing.objects.create(
            area=self.area, address="1 Test Lane", property_type="Detached",
            price=200000, bedrooms=5, bathrooms=4
        )

        #add to users portfolio
        self.portfolio_item = Portfolio.objects.create(
            user=self.user, housing=self.house, status='LIVING', rent_pcm=0
        )
    
    #TEST 1 - GET method - recieved data and code 200
    def test_get_portfolio(self):
        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["total_properties"], 1)
        self.assertEqual(data["my_porfolio"][0]["address"], "1 Test Lane")

    #TEST 2 - POST new portfolio - verify exists and code 201
    def test_new_portfolio(self):
        payload = {
            "create": "True",
            "address": "99 New Street",
            "area_name": "Hackney",
            "property_type": "Flat",
            "price": 300000,
            "status": "RENTING",
            "bedrooms":5, "bathrooms":4
        }
        response = self.client.post('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Portfolio.objects.filter(user=self.user, housing__address="99 New Street").exists())

    #TEST 3 - PUT (update portfolio) - update price and code 200
    def test_update_portfolio(self):
        payload = {
            "address": "1 Test Lane",
            "price": 250000,
            "status": "SELLING"
        }
        response = self.client.put('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        self.house.refresh_from_db()
        self.portfolio_item.refresh_from_db()
        self.assertEqual(self.house.price, 250000)
        self.assertEqual(self.portfolio_item.status, "SELLING")

    #TEST 4 - conflicting - trying to add house already added - error code 409 
    def test_conflict_portfolio(self):
        user2 = User.objects.create_user(username="portfolio_owner2", password="password123", email="port@testmail.com")
        payload = {"username": "portfolio_owner2", "password": "password123", "email": "port@testmail.com"}
        self.client.post('/api/register/', data=json.dumps(payload), content_type='application/json')

        payload = {
            "create": "False",
            "address": "1 Test Lane",
            "status": "LIVING"
        }
        response = self.client.post('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    #TEST 5 - DELETE - property should no longer exist - status code 200
    def test_delete_portfolio(self):
        payload = {"address": "1 Test Lane"}
        response = self.client.delete('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Housing.objects.filter(address="1 Test Lane").exists())

#rating tests
class RatingAPITests(TestCase):
    def setUp(self):
        #create a user then log them in 
        self.client = Client()
        self.user = User.objects.create_user(username="portfolio_owner", password="password123", email="port@testmail.com")
        payload = {"username": "portfolio_owner", "password": "password123"}
        self.client.post('/api/login/', data=json.dumps(payload), content_type='application/json')

        #create a house/area
        self.area = Area.objects.create(name="Camden")
        self.house = Housing.objects.create(
            area=self.area, address="10 Rating Road", property_type="Terraced", 
            price=600000, bedrooms=3, bathrooms=1
        )

        #add to users portfolio
        self.portfolio_item = Portfolio.objects.create(
            user=self.user, housing=self.house, status='LIVING', rent_pcm=0
        )
    
    #TEST 1 - POST create reating - satus code 201
    def test_create_rating(self):
        payload = {"address": "10 Rating Road", "score": 8, "comments": "Lovely place!"}
        response = self.client.post('/api/rate/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Rating.objects.filter(user=self.user, housing=self.house, score=8).exists())

    #TEST 2 - DELETE house therefore rating should not exist
    def test_delete_housing(self):
        payload = {"address": "10 Rating Road"}
        response = self.client.delete('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Rating.objects.filter(user=self.user, housing=self.house).exists())