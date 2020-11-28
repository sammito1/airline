# airline
Simple (mock) airline website built using (but not limited to) Flask, Jinja, and PostgreSQL.

## Installation, Setup

Simply run the setup file as shown:
`$ ./setup.sh`

Set up the database by going into the COSC3380 database and running the following command:

`$ COSC3380=# \i database.sql`

And whenever you want to start the server for the web app, run (preferably in a separate terminal tab):

`$ ./start_server.sh`

Now, you can visit the web app by going to the localhost link given in the output.