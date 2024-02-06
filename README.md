# PBSHM Core
PBSHM Core is a minimal application built on [Flask](https://github.com/pallets/flask) to enable development of PBSHM modules that consume [PBSHM Schema](https://github.com/dynamics-research-group/pbshm-schema) data. It was designed to deal with all the basic requirements of a PBSHM system, allowing developers to focus on implementation of PBSHM modules. 

The application includes a `initialisation` module to configure and set up the system, a `authentication` module to provide permission-based authorisation of controls, a `layout` module to provide an app wide layout, a `timekeeper` module to enable conversion between native python `datetime` objects and the PBSHM Schema `timestamp` format, and finally a `mechanic` module to facilitate easy interaction between available PBSHM Schema versions and your local database. The minimum version of Python required to run the PBSHM Core is version 3.8.10.

For more information on how to create a module for PBSHM Core, please see the [module template](https://github.com/dynamics-research-group/pbshm-module-template) repository.

## Installation
Install the package via pip:
```
pip install pbshm-core
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
The above steps will prompt you for all the required fields to set up the system.

## Running
The application is run via the standard Flask command:
```
flask run
```

## Accessing data
The PBSHM Core operates under the premise of data silos: where each realm of confidential data has a corresponding silo (a *structure collection*) where it's data resides. A user will always have access to at least one *structure collection* (the *default collection*), but there may be multiple *structure collection*s available to the user.

The code below shows how to access data in the *default collection* using a [MongoDB Aggregation Pipeline](https://www.mongodb.com/docs/manual/aggregation/#aggregation-pipelines) on the `default_collection`:

```python
from pbshm.db import default_collection

populations = {}
for document in default_collection().aggregate([
    {"$project":{
        "_id":1,
        "name":1,
        "population":1
    }},
    {"$group":{
        "_id":"$population",
        "structures":{"$addToSet":"$name"}
    }},
    {"$project":{
        "_id":0,
        "population":"$_id",
        "structures":1
    }}
]):
    populations[document["population"]] = document["structures"]
```

## Tools
The PBSHM Core comes with a few tools which are available via the mechanic and timekeeper modules. The mechanic module enables easy interaction with the PBSHM Schema and your local database. The timekeeper module enables conversions from native python `datetime` objects into the `timestamp` format stored within the PBSHM Schema.

To retrieve all versions of the PBSHM Schema available for installation, use the following command:
```
flask mechanic versions
``` 

To create a new collection with the latest version of the PBSHM Schema installed within the collection, use the following command:
```
flask mechanic new-structure-collection collection-name
```

To create a new collection with a specific version of the PBSHM Schema installed within the collection, use the following command:
```
flask mechanic new-structure-collection collection-name --version=v1.0
```

To convert a python `datetime` object into UTC nanoseconds since epoch, use the following code:
```python
from datetime import datetime
from pbshm.timekeeper import datetime_to_nanoseconds_since_epoch

now = datetime.now()
nanoseconds = datetime_to_nanoseconds_since_epoch(now)
```

To convert a UTC nanoseconds since epoch into a native python `datetime` object, use the following code:
```python
from pbshm.timekeeper import nanoseconds_since_epoch_to_datetime

nanoseconds = 1706884924912888000
date_time = nanoseconds_since_epoch_to_datetime(nanoseconds)
```

## Bug reporting
If you encounter any issues/bugs with the system or the instructions above, please raise an issue through the [issues system](https://github.com/dynamics-research-group/pbshm-flask-core/issues) on GitHub.