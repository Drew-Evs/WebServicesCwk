# WebServicesCwk
Using London data to show cost of areas in london/allow users to login and rate different areas. Allow searching for specific price and add parameters for certain housing.

## To Run
### If docker desktop installed
1. Run docker desktop engine
2. Navigate to housing_api folder
3. Run `docker compose up --build`

### If not
1. Naviagte to housing_api folder
2. Run `pip install -r requirements.txt`
3. Run `python manage.py runserver`

## API Documentation
Describes the 5 endpoints:
1. User Account
2. Ratings
3. Housing & Marketplace
4. Portfolio
5. Area <br>
And the GET, POST, PUT & DELETE methods for each one. <br>
Includes example requests, returns, expected response codes and potential error codes. <br>
[API DOCS](<API Documentation.pdf>)
