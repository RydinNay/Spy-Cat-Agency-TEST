# Spy-Cat-Agency-TEST
SCA project

Getting Started

Create a .env file in the main directory based on .env_example

Run the project using Docker Compose:
docker-compose up --build

To use the test version, set in .env:
VERSION=Test

For production, set:
VERSION=Prod

The main difference is that production uses JWT authorization
Using JWT Authorization in Production

In production mode, all API and admin requests must include a valid JWT access token.

Get a pair of tokens:

POST /api/token/
Body:
{
  "email": "your_email",
  "password": "your_password"
}

Refresh the access token:
POST /api/token/refresh/
Body:
{
  "refresh": "your_refresh_token"
}

Use the token in requests:
Add a header to any API or admin request:
Authorization: Bearer your_access_token

JWT authorization is required for:
All API endpoints
Any actions involving agents, missions, or targets

Note: Automatic creation of the superadmin will only work in the test version. In production, you need to create the superadmin manually inside the container.

To create a superadmin manually in production:
docker-compose exec web bash
python manage.py createsuperuser
Follow the prompts to set username, email and password for the superadmin.

API documentation is available at your_ip:your_port/swagger/

Usage:
The SCA project can be used both through the Django admin panel and through API. The rules for creating and editing agents, missions, and targets are the same in both interfaces.

Business Rules:

1) Agents:
Name and breed are read-only after creation
Breed must exist in TheCatAPI
Agents can only be assigned to one active mission at a time (missions with status NOT_STARTED or IN_PROGRESS)
Agents from missions with status DONE or FAILED can be assigned to new missions

2) Missions:
Status is automatically calculated based on target statuses and cannot be changed manually
All targets FAILED -> mission FAILED
All targets DONE or FAILED -> mission DONE
Any target in progress -> mission IN_PROGRESS
Agent can only be assigned or changed if mission status is NOT_STARTED
Targets can only be added when creating a mission; they cannot be added later
Mission status is updated automatically whenever target statuses change

3) Targets:
Name and country are read-only after creation
Notes and status can only be updated if the mission has an agent assigned
Status updates of targets automatically trigger mission status recalculation


Summary:
Admin panel and API follow the same rules for consistency
You can create, update, and view agents, missions, and targets according to the rules above
Business logic is enforced in serializers to prevent inconsistent data
