#
#
#

deploy: samconfig.toml config.json
	cp -a config.json src/config.json
	sam build
	sam deploy

# config.json need to be created by hand...
config.json:
	@echo "No config.json file. Please create it by refering config-sample.json"
	@exit 1

reconfigure:
	$(MAKE) -B samconfig.toml

samconfig.toml:
	sam build
	sam deploy -g --no-execute-changeset

test:
	PYTHONPATH=${PYTHONPAT}:./src python -m pytest tests
