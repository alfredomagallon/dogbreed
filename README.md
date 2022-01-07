# dogbreed

A lightweight example of Dog Breed Identification Service powered by BigAnimal and Tensorflow.

**BigAnimal**: The service uses a BigAnimal PostgreSQL database as the source for images that are used to train the Machine Learning model used to identify the dogs. The database is also used to store the successful and failed identifications (These might well be reused to train and improve model accuracy in a real-life scenario)

**Tensorflow**: At the backend, there is a trained ML model created with Tensorflow, which uses one of the pre-trained model and adds a final layer with the 45 dog breeds.

The service is implemented in three Docker containers, one for the backend and two for the Web UI.

## The beginning: Helper scripts ##

### prepare_files.py ###

This script is used to take all images from the **images** folder, and create a resized copy with a size of 400x400. This helps later in comparing images of the same size.

### upload_files.py ###

Here is where the resized images are stored in the BigAnimal database for further processing. The following environment variables need to be defined:

`DOGBREEDDB_ADDR`: DNS name of the BigAnimal database service (returned when creating the DB cluster in BA)

`DOGBREEDDB_PORT`: Port of the BigAnimal database service (returned when creating the DB cluster in BA)

`DOGBREEDDB_USER`: Typed in BigAnimal during cluster creation

`DOGBREEDDB_PASS`: Typed in BigAnimal during cluster creation

The database needs to include three tables, which can be created with the following DDL code (ddl.txt):

    CREATE DATABASE dogbreed
    \c dogbreed
    CREATE TABLE breeds (id smallint NOT NULL PRIMARY KEY, name varchar(50) NOT NULL)
    CREATE TABLE pictures (breed_id smallint NOT NULL, id smallint NOT NULL, name varchar(255), picture bytea, PRIMARY KEY (breed_id, id))
    CREATE TABLE history (id serial, picture bytea, breed varchar(255), success boolean)

The **psycopg2** python module is used to communicate with the BigAnimal (PostgreSQL) database.

## The backend: dogbreedsvc

Once we have our database full of dog images of the different breeds, we can use those images to train a Machine Learning model to recognize the dogs.

The service loads the images from the database, trains the model with them, and then stays running as a microservice listening to requests from the WebUI.

As we planned to run the service using CPU and a few gigs of RAM, the service uses a pre-trained model called **Xception**. On top of it, there is the final layer with our 45 breeds that the model will predict.

The bootstrap phase of the service perform all the initial tasks of creating and training the model. It takes around 35 minutes on a system without GPU, and uses a maximum of around 6,5 GB RAM.

After the bootstrap, the service stays resident (using Flask for Python framework) providing an endpoint called **/identify** where the pictures need to be submitted for identification. The response will include a success indication along with an array of the different breeds and a percentage for each. If the model is accurate and the image provided belongs to one of the 45 trained breeds, only one of the elements of the array will have a great percentage close to 100%, the rest will have something around 0%.

The following environment variables need to be defined:

`DOGBREEDDB_ADDR`: DNS name of the BigAnimal database service (returned when creating the DB cluster in BA)

`DOGBREEDDB_PORT`: Port of the BigAnimal database service (returned when creating the DB cluster in BA)

`DOGBREEDDB_USER`: Typed in BigAnimal during cluster creation

`DOGBREEDDB_PASS`: Typed in BigAnimal during cluster creation

The service is using the following external python modules:

**psycopg2** to communicate with the BigAnimal PostgreSQL database service

**numpy** to manage great arrays of numbers representing the images

**pillow** for image treatment

**tensorflow** for creating, training and using the ML model for predictions

**flask** to create a microservice using Python code

A Dockerfile and an example of the docker command to run the service are provided in the repository.

## The frontend: dogbreedui

This Web site provides an example of utilization of **dogbreedsvc**.

It allows the user to submit a picture of a dog, and the predicted breed will be returned.

After that, the user can provide feedback whether the prediction was good or bad. This response, among with the dog picture, will be stored in the BigAnimal PostgreSQL database for reference. The Web UI will show the user the latest attempts (also read from the database) after providing feedback (this history page can also be shown by clicking the *See latest attempts* button in the main page)

The current implementation assumes the use of a certificate (i.e. letsencrypt) to enable TLS communication between the WebUI and the user browser. This is intended only to remove ugly alerts during show time, not as part of a production-like security plan :)

The following environment variables need to be defined:

`DOGBREEDDB_ADDR`: DNS name of the BigAnimal database service (returned when creating the DB cluster in BA)

`DOGBREEDDB_PORT`: Port of the BigAnimal database service (returned when creating the DB cluster in BA)

`DOGBREEDDB_USER`: Typed in BigAnimal during cluster creation

`DOGBREEDDB_PASS`: Typed in BigAnimal during cluster creation

`DOGBREEDSVC_ADDR`: DNS name or IP address of the dogbreedsvc microservice

`DOGBREEDSVC_PORT`: Port in which the dogbreedsvc is listening (defaults to 5000)

`DOGBREEDUI_CERT`: Path to the certificate file (defaults to */etc/letsencrypt/live/\<domain-cn\>/cert.pem*) if using letsencrypt certbot in Linux systems)

`DOGBREEDUI_KEY`: Path to the private key file (defaults to */etc/letsencrypt/live/\<domain-cn\>dog-breed.info/privkey.pem* if using letsencrypt certbot in Linux systems)

The UI is using the following external python modules:

**psycopg2** to communicate with the BigAnimal PostgreSQL database service

**pillow** for image treatment

**flask** to create a microservice using Python code

It also uses <a href=https://getbootstrap.com/ target="_blank">Bootstrap</a> to easily improve the Website appearance (while in an amateur way)

A Dockerfile and an example of the docker command to run the UI are provided in the repository.

## dogbreedui_redirect (just a helper)

As we are using a certificate, we use this little Flask application to listen to port 80 (http) and redirect to port 443 (https)

The following environment variable need to be defined:

`DOGBREEDUI_URL`: The *https* URL of the dogbreedui service

The redirect helper is using the following external python modules:

**flask** to create a microservice using Python code

> Written with [StackEdit](https://stackedit.io/).