# FundNJ Where-to-Play

### Overview
This project is a voting system with key features for a secure and fair process.

### Essential Features
1. Hidden Votes: Votes are hidden until a user votes.
2. Form Locking: The form locks after voting.
3. Owner Role: An owner manages the voting process.
4. Team Notifications: Notifies team members to participate.
5. Post-Vote Graph: Displays results graphically after voting.

### Non-essential Features
1. Product/Service Video: Explains the product.
2. Participant Cap: Limit the number of participants.
3. Where to Play: Backup/Growth insights (Slide 16).

##### Notes
Participants: Supports 2 or more users.

### Build

These are the steps to follow to properly initialize this project:

1. Create a virtual environment (run this command from the root folder of your workspace)

   - command: `py -m venv .venv`

2. Activate the virtual environment (this should always be done whenever working on this project)

   - command: `.venv/scripts/activate`

3. Install dependencies

   - command: `pip install -r requirements.txt`
   - IMPORTANT: If you decide to install any further dependencies for this project, make sure
     to run the following command: `py -m pip freeze > requirements.txt`

4. Test that the server runs locally on your machine

   - Run the following command: `py manage.py runserver`
   - By default, and for this project, Django runs on port 8000
   - press CTRL+c to stop the server once you see the default welcome page

5. To deactivate the virtual environment, simply run the command: `deactivate`

6. IMPORTANT ADDITION: You must create and initialize the MySQL database
   - First, run the file dbSchema.sql
   - Second, create a file named `.env` within the `REVyourSTARTUP` directory. This file will contain the appropriate environment variables required for Django to connect to the database. THIS FILE IS PART OF `.gitignore`, and as such it is important that you set it up correctly.
   - Here are the contents of the file:
     ```
     SECRET_KEY=django-insecure-h_g#))0u(28qg&qg))j@#z)p-u90pnfei8zf7t$#b#3u22@#ei
     DATABASE_NAME=revapi
     DATABASE_USER=root
     DATABASE_PASS=YOUR_DATABASE_PASSWORD
     ```
   - Replace DATABASE_PASS with the one you have created on your system for your local MySQL server
   - Initialize the models for the database by running `py manage.py makemigrations` followed by `py manage.py migrate`