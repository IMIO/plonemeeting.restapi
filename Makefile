
buildout_file := buildout.cfg

all: buildout

.PHONY: cleanall
cleanall:
	rm -rf bin develop-eggs include lib local parts/instance1 parts/zeoserver parts/test share .installed.cfg .mr.developper.cfg

.PHONY: bootstrap
bootstrap:cleanall
	virtualenv-2.7 --clear .
	bin/pip install -r requirements.txt

.PHONY: buildout
buildout:bootstrap
	bin/buildout -c ${buildout_file}

.PHONY: test
test:buildout
	bin/python bin/test
