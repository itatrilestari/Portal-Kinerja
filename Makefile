run:
	@./manage.py runserver 0.0.0.0:8000
migrate:
	@./manage.py migrate
makemigrations:
	@./manage.py makemigrations
shell:
	@./manage.py shell_plus
runworker:
	@celery -A config worker -l info -Q kinerja