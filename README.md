# Carpentry.io

Continuous Integration for the People


## Introduction

In 2015 humanity has achieved great advances in technology, the tools
for building software are becoming easier to use.  Projects like
[python requests](http://python-requests.org), grunt, gulp, flask,
they are all open source and easy to use.

Carpentry was born out of the motivation of creating a stable
continuous integration server, and that it made very easy to set up a
build within minutes. It should also automate its own deployment and
help anyone in the world have a simple and functional CI server with
almost no effort.


## Project status

The project is in alpha phase, currently deployed to carpentry.io for
private test only.

More information and documentation coming soon.


## Running it locally


1. You will need a cassandra instance or cluster running
2. Also a redis instance available for the workers :+1:
3. Have bower installed
4. create a virtual env


### 1. run the functional tests to ensure that the system meets all the dependencies

```bash
make dependencies
pip install agile
make test
```

### 2. clear the db, create a local keyspace

```bash
make db
```

### 3. install assets for the web frontend

```bash
make clean
bower install
```

### 4. run the web server

```bash
make run
```

### 5. run an instance of workers

*(pro tip: if you run multiple workers in your machine your builds will run faster)*
```bash
make workers
```
