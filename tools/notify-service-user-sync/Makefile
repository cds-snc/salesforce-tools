default: 
	python3 script.py

fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

lint:
	pylint script.py

test:
	coverage run -m pytest -s -vv tests &&\
	coverage report -m

.PHONY: \
	fmt \
	install	\
	lint \
	test