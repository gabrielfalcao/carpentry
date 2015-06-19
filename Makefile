CWD			:= $(shell pwd)
JACI_CONFIG_PATH	:= $(CWD)/tests/jaci.yml
PYTHONPATH		:= $(CWD)
export JACI_CONFIG_PATH
export PYTHONPATH

all: test

test: unit functional

gunicorn:
	gunicorn wsgi:application --bind 0.0.0.0:5000 --log-level debug

run:
	python jaci/cli.py run

db:
	python jaci/cli.py setup --drop
	python tests/load-fixtures.py

workers:
	python jaci/cli.py workers

unit:
	nosetests -v -s --rednose --with-coverage --cover-erase --cover-package=jaci tests/unit

functional:
	nosetests --stop --logging-level=INFO -v -s --with-coverage --cover-erase --cover-package=jaci --rednose tests/functional

clean:
	rm -rf sandbox
	git clean -Xdf
