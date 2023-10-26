# PBSHM Flask Core
PBSHM Flask Core is a minimal application built on [Flask](https://github.com/pallets/flask) to enable development of PBSHM Modules that consume [PBSHM Schema](https://github.com/dynamics-research-group/pbshm-schema) data. It was designed to deal with all the basic requirements of a PBSHM system, allowing developers to focus on implementation of PBSHM Modules. 

The application includes an initialisation module to setup the system and database, a permission-based user authentication module and a simple graphing module to allow exploration of data within the database. The minimum version of Python required to run the PBSHM Flask Core is version 3.8.10.

## Installation
Install the required python packages via pip:
```
pip install -r requirements.txt
```

## Setup
Set the Flask application path and environment.

For Linux/Mac:
```
export FLASK_APP=pbshm
export FLASK_DEBUG=1
```
For Windows:
```
set FLASK_APP=pbshm
set FLASK_DEBUG=1
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

## Tools
The PBSHM Flask Core comes with a few tools which are available via the mechanic module.

To retrieve all versions of the [PBSHM Schema](https://github.com/dynamics-research-group/pbshm-schema) available for installation, use the following command:
```
flask mechanic versions
``` 

To create a new collection with the latest version of the [PBSHM Schema](https://github.com/dynamics-research-group/pbshm-schema) installed within the collection, use the following command:
```
flask mechanic new-structure-collection collection-name
```

To create a new collection with a specific version of the [PBSHM Schema](https://github.com/dynamics-research-group/pbshm-schema) installed within the collection, use the following command:
```
flask mechanic new-structure-collection collection-name --version=v1.0
```