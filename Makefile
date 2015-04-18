all: test

test: unit functional

gunicorn:
	gunicorn wsgi:application --bind 0.0.0.0:5000 --log-level debug

run:
	tumbler run --port=5000 jaci/routes.py --templates-path=`pwd`/templates --static-path=`pwd`/jaci/static

unit:
	nosetests -v -s --rednose --with-coverage --cover-erase --cover-package=jaci tests/unit

functional:
	nosetests --stop --logging-level=INFO -v -s --with-coverage --cover-erase --cover-package=jaci --rednose tests/functional
