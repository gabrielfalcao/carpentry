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
	python jaci/cli.py static

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
	rm -rf sandbox dist
	git clean -Xdf
	make assets

release: assets
	./.release

deploy-web:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.jaci -t upstart -t jaci-workers deployment/jaci-io.yml

deploy-workers:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.jaci -t upstart -t jaci-web deployment/jaci-io.yml

deploy-from-scratch:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.jaci --extra-vars="jaci_recreate_keyspace=yes" deployment/jaci-io.yml

deploy-all:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.jaci deployment/jaci-io.yml

deploy-nginx:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.jaci -t nginx deployment/jaci-io.yml

deploy: deploy-all
