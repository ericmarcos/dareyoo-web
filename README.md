#dareyoo-web
This repo contains the Dareyoo backend/API (Django) and the web app (AngularJS).

#Developement environment

##Dependencies

* Python 2.7.x and pip
* virtualenvwrapper
* PostgreSQL (you can use SQLite, but I encourage you to use Postgres as it's what is used in production)
* RabbitMQ
* NodeJS
* Bower
* Gulp

To install virtualenvwrapper do `pip install virtualenvwrapper` and add these lines to your .bashrc:
```
export WORKON_HOME=~/.virtualenvs (or whatever you like)
source /usr/local/bin/virtualenvwrapper.sh
```

then source your .bashrc to activate these lines.

##Create a DB
Create a database and a database user in PostgreSQL

##Preparing the virtual environment

After cloning this repo, create a python virtualenv:
`mkvirtualenv dareyoo`

this will create an isolated python virtual environment, so we can install all our dependencies without clashing with the current system libs and other projects.

`deactivate` to exit the virtualenv and edit ~/.virtualenvs/dareyoo/bin/postactivate:

```bash
#!/bin/bash
# This hook is run after this virtualenv is activated.

export PROJECT_NAME=dareyoo
export PROJECT_HOME=~/Documents/dareyoo/dareyoo-web [REPLACE BY YOUR PROJECT DIR]
cd $PROJECT_HOME
export DATABASE_URL=postgres://[DB_USERNAME]:[DB_PASSWORD]@localhost:5432/[DB_NAME]
export STATIC_URL=/static/
export AUTO_QUEUE_DEADLINES=1
export GENERATE_NOTIFICATIONS=1
export DEBUG=1
alias django='python $PROJECT_HOME/manage.py'
alias cr='django celery -A dareyoo worker -B -l info'
```

Now `workon dareyoo` and you'll be ready to go.

##Installing python dependencies

`pip install -r requirements.txt`

##Sync DB

To create the tables in the database just run:

```
django syncdb
django migrate
```

It will prompt you for an admin user, you can create one if you want.

##Run developement web server

`django runserver` and visit http://127.0.0.1:8000, you should see Dareyoo's landing page.

##Run developement tasks server

`cr` and leave that console open. It will handle periodic and delayed tasks like closing bets, refilling yoos, etc.

##Preparing the frontend environment

From the project's root dir run:
```
npm install
npm install -g bower
bower install
```
