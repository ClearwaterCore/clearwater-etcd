ENV_DIR := $(shell pwd)/_env
ENV_PYTHON := ${ENV_DIR}/bin/python
PYTHON_BIN := $(shell which python)

DEB_COMPONENT := clearwater-etcd
DEB_MAJOR_VERSION := 1.0${DEB_VERSION_QUALIFIER}
DEB_NAMES := clearwater-etcd clearwater-cluster-manager clearwater-config-manager clearwater-management
DEB_ARCH := all

# The build has been seen to fail on Mac OSX when trying to build on i386. Enable this to build for x86_64 only
X86_64_ONLY=0

.DEFAULT_GOAL = deb

.PHONY: fvtest
fvtest: fvtest_setup.py env
	PYTHONPATH=src:common ${ENV_PYTHON} fvtest_setup.py test -v

.PHONY: test
test: cluster_mgr_setup.py env
	PYTHONPATH=src:common ${ENV_PYTHON} cluster_mgr_setup.py test -v

${ENV_DIR}/bin/flake8: env
	${ENV_DIR}/bin/pip install flake8

${ENV_DIR}/bin/coverage: env
	${ENV_DIR}/bin/pip install coverage

verify: ${ENV_DIR}/bin/flake8 alarms
	${ENV_DIR}/bin/flake8 --select=E10,E11,E9,F src/

style: ${ENV_DIR}/bin/flake8 alarms
	${ENV_DIR}/bin/flake8 --select=E,W,C,N --max-line-length=100 src/

explain-style: ${ENV_DIR}/bin/flake8 alarms
	${ENV_DIR}/bin/flake8 --select=E,W,C,N --show-pep8 --first --max-line-length=100 src/

.PHONY: coverage
coverage: ${ENV_DIR}/bin/coverage cluster_mgr_setup.py
	rm -rf htmlcov/
	${ENV_DIR}/bin/coverage erase
	${ENV_DIR}/bin/coverage run --source src --omit "**/test/**"  cluster_mgr_setup.py test
	${ENV_DIR}/bin/coverage report -m
	${ENV_DIR}/bin/coverage html

.PHONY: env
env: cluster_mgr_setup.py config_mgr_setup.py shared_setup.py $(ENV_DIR)/bin/python build-eggs alarms

$(ENV_DIR)/bin/python:
	# Set up the virtual environment
	virtualenv --setuptools --python=$(PYTHON_BIN) $(ENV_DIR)
	$(ENV_DIR)/bin/easy_install "setuptools>0.7"
	$(ENV_DIR)/bin/easy_install distribute

include build-infra/cw-deb.mk

.PHONY: config-mgr-build-eggs
config-mgr-build-eggs: config_mgr_setup.py shared_setup.py common/setup.py src
	# Generate .egg files
	${ENV_DIR}/bin/python config_mgr_setup.py bdist_egg -d config_mgr_eggs
	${ENV_DIR}/bin/python shared_setup.py bdist_egg -d config_mgr_eggs
	cd common && ${ENV_DIR}/bin/python setup.py bdist_egg -d ../config_mgr_eggs

	# Download the egg files they depend upon
	${ENV_DIR}/bin/easy_install -zmaxd config_mgr_eggs/ config_mgr_eggs/clearwater_config_manager-1.0-py2.7.egg
	${ENV_DIR}/bin/easy_install -zmaxd config_mgr_eggs/ config_mgr_eggs/clearwater_etcd_shared-1.0-py2.7.egg
	${ENV_DIR}/bin/easy_install -zmaxd config_mgr_eggs/ config_mgr_eggs/metaswitchcommon-0.1-py2.7.egg

.PHONY: build-eggs
build-eggs: cluster-mgr-build-eggs config-mgr-build-eggs

.PHONY: cluster-mgr-build-eggs
cluster-mgr-build-eggs: cluster_mgr_setup.py shared_setup.py common/setup.py src
	# Generate .egg files
	${ENV_DIR}/bin/python cluster_mgr_setup.py bdist_egg -d cluster_mgr_eggs
	${ENV_DIR}/bin/python shared_setup.py bdist_egg -d cluster_mgr_eggs
	cd common && ${ENV_DIR}/bin/python setup.py bdist_egg -d ../cluster_mgr_eggs

	# Download the egg files they depend upon
	${ENV_DIR}/bin/easy_install -zmaxd cluster_mgr_eggs/ cluster_mgr_eggs/clearwater_cluster_manager-1.0-py2.7.egg
	${ENV_DIR}/bin/easy_install -zmaxd cluster_mgr_eggs/ cluster_mgr_eggs/clearwater_etcd_shared-1.0-py2.7.egg
	${ENV_DIR}/bin/easy_install -zmaxd cluster_mgr_eggs/ cluster_mgr_eggs/metaswitchcommon-0.1-py2.7.egg

alarms: 
	python common/metaswitch/common/alarms_writer.py --json-file="clearwater-config-manager.root/usr/share/clearwater/infrastructure/alarms/clearwater_config_manager_alarms.json" --constants-file="src/metaswitch/clearwater/config_manager/alarm_constants.py"
	python common/metaswitch/common/alarms_writer.py --json-file="clearwater-cluster-manager.root/usr/share/clearwater/infrastructure/alarms/clearwater_cluster_manager_alarms.json" --constants-file="src/metaswitch/clearwater/cluster_manager/alarm_constants.py"

.PHONY: deb
deb: env build-eggs deb-only

.PHONY: clean
clean: envclean pyclean

.PHONY: pyclean
pyclean:
	find src -name \*.pyc -exec rm -f {} \;
	rm -rf src/*.egg-info dist
	rm -f .coverage
	rm -rf htmlcov/

.PHONY: envclean
envclean:
	rm -rf bin cluster_mgr_eggs config_mgr_eggs develop-eggs parts .installed.cfg bootstrap.py .downloads .buildout_downloads *.egg .eggs *.egg-info
	rm -rf distribute-*.tar.gz
	rm -rf $(ENV_DIR)

