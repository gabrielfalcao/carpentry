CWD			:= $(shell pwd)
JACI_CONFIG_PATH	:= $(CWD)/tests/jaci.yml
JACI_WORKDIR		:= $(CWD)/sandbox
JACI_LOG_PATH		:= $(CWD)/jaci.log
PYTHONPATH		:= $(CWD)
export JACI_CONFIG_PATH
export JACI_LOG_PATH
export PYTHONPATH

all: test

test: unit functional

gunicorn: assets
	gunicorn jaci.wsgi:application --bind 0.0.0.0:5000 --log-level debug --workers=10

assets:
	bower install
run:
	python jaci/cli.py run

dependencies:
	pip install -U pip
	pip install -r requirements.txt

db:
	python jaci/cli.py setup --drop --flush-redis
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


release: test assets
	./.release
