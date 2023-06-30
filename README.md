`bm2` is a public iteration of my personal bookmarks site.

---

## Usage

I generally use `pipenv` for Python/Django projects because it's familiar.
You can adopt the usage instructions below to a different tool if that's more your jam.

Getting this running locally is pretty straight forward.

Install the dependencies:

```
pipenv install
```

Generate a secure Django secret key and add it to `.env`:

```
echo "DJANGO_SECRET_KEY=<secret!>" > .env
```

Run the initial migrations to setup the database:

```
pipenv run python manage.py migrate
```

There's currently no way to create an account through the web interface, so use the CLI to create a user:

```
pipenv run python manage.py createsuperuser
```

Running the development server:

```
pipenv run python manage.py runserver
```

### Running the tests

```
pipenv run python manage.py test
```

### Deploying to a VPS

Notes:

- Ansible must be installed on your local machine
- Target should be running Ubuntu 22.04
- The domain that you are deploying to must be in `ALLOWED_HOSTS`

```
pipenv run python manage.py up <your-domain> --email=<your-email>
```

### Checks

A [pre-commit](https://pre-commit.com) configuration is available that runs the same checks as the Github Actions pipeline.

```
pre-commit install
```

There checks can be manually run with:

```
pre-commit run --all-files
```

---

Generated with [sesh/djbs](https://github.com/sesh/djbs).
