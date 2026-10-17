.PHONY: up down status seed test-queries test-sim test-race check-vector api web test-agents bench

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

api:
	python tasks.py api

web:
	python tasks.py web

test-agents:
	python tasks.py test-agents

bench:
	python tasks.py bench
