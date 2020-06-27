# PBSHM Flask Core
PBSHM Flask Core is a minimal application built on [Flask](https://github.com/pallets/flask) to enable development of PBSHM Modules that consume [PBSHM Schema](https://github.com/dynamics-research-group/pbshm-schema) data. It was designed to deal with all the basic requirements of a PBSHM system, allowing developers to focus on implementation of PBSHM Modules. 

The application includes an initialisation module to setup the system and database, a permission-based user authentication module and a simple graphing module to allow exploration of data within the database.

## Installation
Install the required python packages via pip:
```
pip install -r requirements.txt
```

## Setup
Set the Flask application path and environment:
```
set FLASK_APP=pbshm
set FLASK_ENV=development
```

Configure settings and initialise the database with a new root user:
```
flask init config
flask init db new-root-user
```
The above steps will prompt you for all the required fields to setup the system.

## Running
The application is run via the standard Flask command:
```
flask run
```