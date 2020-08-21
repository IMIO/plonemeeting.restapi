
buildout_file := buildout.cfg

all: buildout

.PHONY: cleanall
cleanall:
	rm -rf bin develop-eggs include lib local parts/instance1 parts share .installed.cfg .mr.developper.cfg

.PHONY: bootstrap
bootstrap:cleanall
	virtualenv --clear .
	bin/python bin/pip install -r https://raw.githubusercontent.com/IMIO/buildout.pm/master/requirements.txt

.PHONY: buildout
buildout:bootstrap
	bin/buildout -c ${buildout_file}

.PHONY: test
test:buildout
	bin/python bin/test

