# airline
Simple (mock) airline website built using (but not limited to) Flask, Jinja, and PostgreSQL.

## Demo Video
[Click here](https://streamable.com/0o14pz) to watch a demo video of the app in action as of December 10th, 2020.

## Installation, Setup
This app runs best on python 3.7 and above, so please have that installed.

Please make a `password.txt` file with your unix id in the top line and your password in the bottom line. You should have it in the same directory as `airline.py`.
Simply run the setup file as shown:

```$ ./setup.sh```

And whenever you want to start the server for the web app, run (preferably in a separate terminal tab):

```$ ./start_server.sh```

Now, you can visit the web app by going to the localhost link given in the output.

If the setup file didn't work, please attempt to install the packages needed manually in pip3. The setup file may not work for those trying to run this on windows.