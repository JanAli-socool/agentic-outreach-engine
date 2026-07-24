.PHONY: install run eval test docker-build docker-run clean

install:
	pip install -r requirements.txt

run:
	python -m scripts.run_single vercel.com

eval:
	python -m scripts.run_evals

test:
	pytest tests/ -v

docker-build:
	docker compose build

docker-run:
	docker compose run --rm agent

docker-eval:
	docker compose run --rm agent python -m scripts.run_evals

clean:
	rm -rf logs/*.json __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +