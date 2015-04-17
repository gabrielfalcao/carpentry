all: test

test: unit functional

run:
	gunicorn wsgi:application --bind 0.0.0.0:5000

unit:
	nosetests -v -s --rednose --with-coverage --cover-erase --cover-package=jaci tests/unit

functional:
	nosetests --stop --logging-level=INFO -v -s --with-coverage --cover-erase --cover-package=jaci --rednose tests/functional


deploy:
	git sync
	floresta vpcs/jaci.yml --yes --inventory-path="inventory" --ansible -vvvv --tags=refresh -M library -u ubuntu --extra-vars='{"github_token":"$(GITHUB_TOKEN)"}'
