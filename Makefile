#
#
#

deploy: samconfig.toml
	sam build
	sam deploy

reconfigure:
	$(MAKE) -B samconfig.toml

samconfig.toml:
	sam build
	sam deploy -g --no-execute-changeset
