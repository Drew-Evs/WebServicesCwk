# London Housing API
## Overview
Designing an API to interact with a database, storing information on housing in London, e.g. price and owner. Allows users to login, view houses, edit and update the database, and buy/rent houses. Further allows users to rate houses and aggregates price/rating data across areas. For example, a user should be able to create an account login and add houses to their portfolio, update information and view others information. Or be able to rent/buy from someone else portfolio. <br>

The architecture is a Django/python backend for the APIs, which communicate with an SQLite database, and a front end via JSON data. The application is packaged by a docker container, and hosted by railway. <br>


## To Run
### Railway URL
https://webservicescwk-production.up.railway.app/api/

### If docker desktop installed
Use if want to run locally. <br>
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

[API Documentation](<API Documentation.pdf>)

## Technical Report
Has the following sections:
1. Architecture Overview
2. Security and Testing
3. Challenges, Limitations and Future Development
4. Generative AI Declaration

[Technical Report](<Technical Report.pdf>)

