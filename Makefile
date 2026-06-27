.PHONY: install run db-up db-down test migrate migrate-init

install:
	cd backend && pip install -r requirements.txt

db-up:
	docker-compose up -d db

db-down:
	docker-compose down

run:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && python -m pytest tests/ -v

migrate-init:
	cd backend && alembic revision --autogenerate -m "initial"

migrate:
	cd backend && alembic revision --autogenerate -m "$(msg)"

migrate-up:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1
