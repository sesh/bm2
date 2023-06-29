`bm2` is a public iteration of my personal bookmarks site.

---

## Usage

I generally use `pipenv` for Python/Django projects because it's familiar.
You can adopt the usage instructions below to a different tool if that's more your jam.

### Running the initial migrations

```bash
pipenv run python manage.py migrate
```

### Running the development server

```bash
pipenv run python manage.py runserver
```

### Running the tests

```bash
pipenv run python manage.py test
```

### Deploying to a VPS

Notes:

- Ansible must be installed on your local machine
- Target should be running Ubuntu 22.04

```bash
pipenv run python manage.py up bm2.brntn.me --email=<your-email>
```

### Checks

```
bandit -c pyproject.toml -r .
```

```
black .
```

---

Generated with [sesh/djbs](https://github.com/sesh/djbs).
