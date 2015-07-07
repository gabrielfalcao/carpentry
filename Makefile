CWD			:= $(shell pwd)
CARPENTRY_CONFIG_PATH	:= $(CWD)/tests/carpentry.yml
CARPENTRY_WORKDIR		:= $(CWD)/sandbox
CARPENTRY_LOG_PATH		:= $(CWD)/carpentry.log
PYTHONPATH		:= $(CWD)
export CARPENTRY_CONFIG_PATH
export CARPENTRY_LOG_PATH
export PYTHONPATH

all: test

test: docker-test unit functional

gunicorn: assets
	gunicorn carpentry.wsgi:application --bind 0.0.0.0:5000 --log-level debug --workers=10

assets:
	bower install
	python carpentry/cli.py static

run:
	python carpentry/cli.py run

dependencies:
	pip install -U pip
	pip install -r requirements.txt

db:
	python carpentry/cli.py setup --drop --flush-redis


workers:
	python carpentry/cli.py workers

unit:
	nosetests -v -s --rednose --with-coverage --cover-erase --cover-package=carpentry tests/unit

functional:
	nosetests --stop --logging-level=INFO -v -s --with-coverage --cover-erase --cover-package=carpentry --rednose tests/functional

clean:
	rm -rf sandbox dist
	git clean -Xdf
	make assets

release: assets
	./.release

deploy-web:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.carpentry -t update-code -t upstart -t carpentry-workers deployment/carpentry-io-native.yml

deploy-workers:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.carpentry -t update-code -t upstart -t carpentry-web deployment/carpentry-io-native.yml

deploy-from-scratch:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.carpentry --extra-vars="carpentry_recreate_keyspace=yes" deployment/carpentry-io-native.yml

deploy-all:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.carpentry deployment/carpentry-io-native.yml

production-db-reset:
	ansible-playbook -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.carpentry -t flush deployment/carpentry-io-native.yml

deploy-nginx:
	ansible-playbook -vvvv -i deployment/inventory.ini --vault-password-file=~/.ansible-vault.carpentry -t update-code -t nginx deployment/carpentry-io-native.yml

deploy: deploy-all
