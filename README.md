`bm2` is a public iteration of my personal bookmarks site.

---

## About

This project exists primarily for two reasons:

- I use it, deployed to bm2.brntn.me, to bookmark sites and manage those bookmarks
- As a playground for me to experiment with techniques, tools and practices

There's are many examples of the former. I was a long-time Pinboard user, and a del.icio.us user before that.
For the later, this codebase hits a bunch of things I like:

- Uses the steps in my "[Six things I do every time I start a Django project][six-things]" post (automated with my poorly-documented `[djbs][djbs]` script)
- Runs the "[Open source Python CI pipeline][ci]" in Github Actions
- Takes a testing approach that relies heavily on [integration tests][integration-tests] ran with the Django test runner
- The majority of new code is added with [Test Driven Development][tdd] and a [trunk-based][tbd] workflow
- Uses my [django-middleware][middleware] and [django-authuser][authuser] projects
- Deploys with [Django Up][up] onto a VPS
- Takes a HTML-first approach with no Javascript
- Gets an A+ on [Security Headers][headers] and the [SSL Labs Report][ssl] (June 2023)

  [six-things]: https://brntn.me/blog/six-things-i-do-every-time-i-start-a-django-project/
  [ci]: https://brntn.me/blog/open-source-python-ci/
  [integration-tests]: https://brntn.me/blog/types-of-testing-you-should-care-about-integration-testing/
  [middleware]: https://github.com/sesh/django-middleware
  [authuser]: https://github.com/sesh/django-authuser
  [up]: https://github.com/sesh/django-up
  [tdd]: https://www.martinfowler.com/bliki/TestDrivenDevelopment.html
  [tbd]: https://martinfowler.com/articles/branching-patterns.html
  [headers]: https://securityheaders.com/?q=bm2.brntn.me&followRedirects=on
  [ssl]: https://www.ssllabs.com/ssltest/analyze.html?d=bm2.brntn.me&latest
  [djbs]: https://github.com/sesh/djbs


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
