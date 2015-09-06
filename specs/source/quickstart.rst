.. _quickstart:

Quickstart
==========

1. you will need a `redis`_ server

.. highlight:: bash


Step 1: Install Carpentry
-------------------------

Perhaps you want to create a `virtualenv`_ first.
::

   $ pip install carpentry


Step 2: Prepare a local redis
-------------------------------------------

**This is going to be easier than you think**


On Mac OSX
""""""""""
You will need `homebrew`_ installed in your Mac::

  $ brew install redis


On Linux
""""""""
The easiest way is through `docker`_::

  $ docker run -d --net=host redis


Step 3: Create the configuration file
-------------------------------------

.. highlight:: yaml

You have a few options as to where place your configuration file.

Carpentry will look for the configuration in the following paths, ir
order:

1. **/etc/carpentry.yml**
2. **$HOME/carpentry.yml**
3. **$HOME/.carpentry.yml**
4. **$(pwd)/carpentry.yml**
5. **$(pwd)/.carpentry.yml**
6. Read the path from the environment variable ``CARPENTRY_CONFIG_PATH``

::

    # /srv/carpentry.yml
    full_server_url: http://localhost:5000
    http_host: localhost
    http_port: 5000
    redis_host: localhost
    redis_port: 6379
    redis_db: 0
    workdir: sandbox
    carpentry_secret_key: something secret
    github_client_id: go to githup and create an app
    github_client_secret: then put the credentials here

    # only users from the organizations below will have access at all
    allowed_github_organizations:
      - cnry

    # optionally enable carpentry to anyone
    public_access: yes

.. highlight:: bash


Step 4: Run the server
----------------------

::

    $ carpentry run


Step 5: Run the workers
-----------------------

::

    $ carpentry workers

.. note::
   pro tip: if you run multiple workers in your machine your builds will run faster

.. _redis: http://redis.io/
.. _bower: http://bower.io/
.. _homebrew: http://brew.sh
.. _virtualenv: https://virtualenvwrapper.readthedocs.org/
