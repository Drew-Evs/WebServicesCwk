import json
from django.test import TestCase, Client
from django.contrib.auth.models import User 
from .models import Housing, Area, Portfolio, Rating, Rent

class HousingAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.area = Area.objects.create(name="Test Area")
        self.house = Housing.objects.create(
            area=self.area, address="123 Fake Street", property_type="Detached",
            price=50000, bedrooms=2, bathrooms=1
        )

    def test_get_housing(self):
        response = self.client.get('/api/housing/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["meta"]["total_results"], 1)

    def test_new_housing(self):
        payload = {"area_name": "New Test Area", "address": "99 Automated Ave", "price": 250000, "bedrooms": 2, "bathrooms": 1}
        response = self.client.post('/api/housing/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Housing.objects.filter(address="99 Automated Ave").exists())

class AuthAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@testmail.com", password="password123")

    def test_register_user(self):
        payload = {"username": "newuser", "password": "securepwd", "email": "new@test.com"}
        response = self.client.post('/api/user/register/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_duplicate_user(self):
        payload = {"username": "testuser", "password": "password123"}
        response = self.client.post('/api/user/register/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 409)
    
    def test_login_user(self):
        payload = {"username": "testuser", "password": "password123"}
        response = self.client.post('/api/user/login/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_logout_user(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/user/logout/')
        self.assertEqual(response.status_code, 200)

    def test_update_account(self):
        self.client.force_login(self.user)
        payload = {"email": "updated@testmail.com"}
        response = self.client.put('/api/user/update/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@testmail.com")

    def test_delete_account(self):
        self.client.force_login(self.user)
        payload = {"username": "testuser"}
        response = self.client.delete('/api/user/update/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="testuser").exists())

class PortfolioAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="portfolio_owner", password="password123")
        self.client.force_login(self.user)
        self.area = Area.objects.create(name="Chelsea")
        self.house = Housing.objects.create(area=self.area, address="1 Test Lane", price=200000, bedrooms=3, bathrooms=2)
        self.portfolio_item = Portfolio.objects.create(user=self.user, housing=self.house, status='LIVING')
    
    def test_get_portfolio(self):
        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, 200)

    def test_new_portfolio(self):
        payload = {"create": "True", "address": "99 New Street", "area_name": "Hackney", "bedrooms": 2, "bathrooms": 1}
        response = self.client.post('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_update_portfolio(self):
        payload = {"address": "1 Test Lane", "status": "SELLING"}
        response = self.client.put('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_delete_portfolio(self):
        payload = {"address": "1 Test Lane"}
        response = self.client.delete('/api/portfolio/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)

class RatingAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="rater", password="password123")
        self.client.force_login(self.user)
        self.area = Area.objects.create(name="Camden")
        self.house = Housing.objects.create(area=self.area, address="10 Rating Road", price=600000, bedrooms=2, bathrooms=1)
    
    def test_get_ratings(self):
        Rating.objects.create(user=self.user, housing=self.house, score=9)
        response = self.client.get('/api/rate/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["total_results"], 1)

    def test_create_rating(self):
        payload = {"address": "10 Rating Road", "score": 8, "comments": "Lovely!"}
        response = self.client.post('/api/rate/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201)

class AreaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.area = Area.objects.create(name="Islington", average_price=500000)

    def test_get_areas(self):
        response = self.client.get('/api/areas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["total_areas_found"], 1)

class HouseBuyAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="buyer", password="password123")
        self.client.force_login(self.user)
        self.area = Area.objects.create(name="Sutton")
        self.house = Housing.objects.create(area=self.area, address="2 Buy Street", price=300000, for_sale=True, bedrooms=4, bathrooms=2)

    def test_get_houses_for_sale(self):
        response = self.client.get('/api/housing/buy/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["total"], 1)

    def test_buy_house(self):
        payload = {"address": "2 Buy Street"}
        response = self.client.post('/api/housing/buy/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.house.refresh_from_db()
        self.assertFalse(self.house.for_sale)
        self.assertTrue(Portfolio.objects.filter(user=self.user, housing=self.house).exists())

class HouseRentAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.landlord = User.objects.create_user(username="landlord", password="password123")
        self.tenant = User.objects.create_user(username="tenant", password="password123")
        self.client.force_login(self.tenant)
        self.area = Area.objects.create(name="Ealing")
        self.house = Housing.objects.create(area=self.area, address="3 Rent Ave", price=400000, for_rent=True, bedrooms=1, bathrooms=1)
        self.portfolio = Portfolio.objects.create(user=self.landlord, housing=self.house, status='RENTING', rent_pcm=1500)

    def test_get_houses_for_rent(self):
        response = self.client.get('/api/housing/rent/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["total"], 1)

    def test_rent_house(self):
        payload = {"address": "3 Rent Ave", "rent_pcm": 1500}
        response = self.client.post('/api/housing/rent/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Rent.objects.filter(tenant=self.tenant).exists())

    def test_update_rent(self):
        Rent.objects.create(housing=self.portfolio, tenant=self.tenant, actual_rent_pcm=1500, active=True)
        payload = {"address": "3 Rent Ave", "new_rent_pcm": 1600}
        response = self.client.put('/api/housing/rent/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Rent.objects.get(tenant=self.tenant).actual_rent_pcm, 1600)

    def test_delete_tenancy(self):
        Rent.objects.create(housing=self.portfolio, tenant=self.tenant, actual_rent_pcm=1500, active=True)
        payload = {"address": "3 Rent Ave"}
        response = self.client.delete('/api/housing/rent/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Rent.objects.filter(tenant=self.tenant).exists())