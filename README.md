Aukigo-backend
===================
![](https://github.com/GispoCoding/aukigo-backend/workflows/Tests/badge.svg)

The structure partly inspired by [ngz-geoviz](https://github.com/GispoCoding/ngz-geoviz/tree/master/ngz-geoviz).

# Installation

Install Docker and docker-compose

### Development mode

Start the backend with:

```shell script
docker-compose -f docker-compose.yml up -d --build
``` 

Django can be accessed from http://localhost:8001/ and pg_tileserv from http://localhost:7800


### Production mode
1. Fill the following environmental variables to the .env file (same directory as docker-compose.yml).
You can copy the .env.dev to get started. 
Database name, password and user could be anything, remember to use your own 
host instead of localhost if using other host.

    ```shell script
    DEBUG=0
    HTTPS=0
    SECRET_KEY=very-secure-password
    USE_S3=0 
    DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
   
       
    SQL_DATABASE=covid_19_dev
    SQL_USER=covid_19_dev_user
    SQL_PASSWORD=covid_19_pwd
    SQL_HOST=localhost
    SQL_PORT=5434
    DATABASE=postgres
    
    DJANGO_SUPERUSER_USERNAME=admin
    DJANGO_SUPERUSER_PASSWORD=very-secure-password
    DJANGO_SUPERUSER_EMAIL=your.email@domain.com
   
    PG_TILESERV_POSTFIX=/tiles
    OSM_SCHEDULE_MINUTES=720
    ```

2. Spin up the app in production mode:

    ```shell script
    docker-compose -f docker-compose.prod.yml up -d --build
    ```

Nginx should now be listening on port 80.

#### Https configuration
Easiest way is to have the certificates on the host and add them as volumes to the host.
* Follow the [Certbot](https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx) instructions to get the certificates
* Uncomment the line `- /etc/letsencrypt:/etc/letsencrypt` in docker-compose.prod.yml
* Modify .env to contain right host in DJANGO_CORS_WHITELIST (DJANGO_CORS_WHITELIST=https://your.url.com http://localhost:8080 http://localhost:8000)
* Set HTTPS=1 in .env 
* Edit all occurences of `server_name` in nginx/nginx_https.conf to match your site
* Replace *nginx/nginx.conf* with *nginx/nginx_https.conf*, and run:

```shell script
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

Nginx should now be listening on port 443.
