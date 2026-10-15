.PHONY: up down status seed test-queries test-sim test-race check-vector

up:
	python tasks.py up

down:
	python tasks.py down

status:
	python tasks.py status

seed:
	python tasks.py seed

test-queries:
	python tasks.py test-queries

test-sim:
	python tasks.py test-sim

test-race:
	python tasks.py test-race

check-vector:
	python tasks.py check-vector
