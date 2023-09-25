# Django App: fusus_app

This Django application provides a comprehensive user and organization management system. It consists of two main models: Organization and User. Organizations serve as entities to group users, and the User model represents individuals belonging to these organizations. Users come with specific roles such as Administrator, Viewer, and the standard User. Each role has different permissions for CRUD operations on the models.

## Table of Contents
- [Setup Environment](#setup-environment)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
  
## Setup Environment

1. Clone the repository:
    ```bash
    git clone https://github.com/sowbobo12000/fusus_django.git
    ```

2. Navigate to the project directory:
    ```bash
   ## dev environment
    cd fusus/test
   
   ## prod environment
   cd fusus/
    ```

3. Run Docker Container
    ```bash
    ## dev
   docker-compose -f docker-compose-dev.yml build --no-cache
   docker-compose -f docker-compose-dev.yml up -d
   
   ## prod
   docker-compose build --no-cache
   docker-compose up -d
    ```
   
4. Run Migration for Production (Auto migration for Dev)
    ```bash
   ## Wait For 15 seconds after starting the django container
    docker exec -it fusus-web-1 /bin/bash
    python manage.py migrate
    ```
5. Down the docker container
    ```bash
    ## dev
   docker-compose -f docker-compose-dev.yml down -v
   
   ## prod
   docker-compose down -v
    ```

## API Endpoints

### Auth Endpoints:

API supports JWT authentication.  
1. **[POST]** `/api/auth/login/`: Authenticate using email address.  
2. **[GET]** `/api/auth/groups/`: Returns authentication groups.  
   - **Administrator**: Full access to CRUD any user in his organization and RU Organization.  
   - **Viewer**: List and retrieve any user in his organization.  
   - **User**: CRU his own user details.  

### User Endpoints:

1. **[GET]** `/api/users/`: List all users within the authenticated user's organization (only if the user is `Administrator` or `Viewer`). Supports search by name, email, and filter by phone.  
2. **[GET]** `/api/users/{id}/`: Retrieve specific user's information, including organization ID and name.  
3. **[POST]** `/api/users/`: Create a new user for the organization. The request user must be an Administrator.  
4. **[PATCH]** `/api/users/{id}`: Update information of the user if the request user is an `Administrator` or the user himself.  
5. **[DELETE]** `/api/users/{id}`: Delete a user. Accessible only by the `Administrator` of his organization.  

### Organization Endpoints:

1. **[GET]** `/api/organizations/{id}/`: Retrieve information of a specific organization if the request user is an `Administrator` or `Viewer`.  
2. **[PATCH]** `/api/organizations/{id}`: Update organization details. Only accessible by `Administrator`.  
3. **[GET]** `/api/organization/{id}/users`: List all users in a specific organization. Returns just user ID and name.  
4. **[GET]** `/api/organization/{id}/users/{id}/`: Retrieve specific user's ID and name within an organization.  

### Other Endpoints:

1. **[GET]** `/api/info/`: Returns system details such as authenticated user's name, ID, organization name, and server's public IP.

### Testing

2. Run the tests:
    ```bash
   cd fusus/test
   docker-compose -f docker-compose-dev.yml down -v
   docker-compose -f docker-compose-dev.yml build --no-cache
   docker-compose -f docker-compose-dev.yml up -dev
   docker ps 
   docker exec -it test-web-1 /bin/bash
   python manage.py test user org
    ```
