# madden-cfm-chatbot
Madden Connected Franchise GroupMe chat bot

The Madden CFM groupme chatbot enables Madden CFM players to be connected to their league without being on their system.

## Installation
Below you will find instructions to install our GroupMe chatbot for your league.

### Create GroupMe Bot
Login at https://dev.groupme.com/session/new
1. Click create bot
2. Select the group in which to add the bot
3. Name the bot (e.g. John Madden)
4. Set callback url (https://NAME-OF-HEROKU-APP.herokuapp.com/)
5. Set bot avatar image
6. Click submit
7. Make not of the group id
8. Click access token in the top right and make not of that value as well

### Create GitHub Account
Create a GitHub account at github.com.
1. Choose the free plan
2. Comeback to this repo (https://github.com/vinniemo90/madden-cfm-chatbot) and fork

### Create Firebase Account
Create firebase account at https://firebase.google.com.
1. Go to console and add project
2. Enter project name and create project
3. Under the develop tab select database
4. Scroll down and chaoose create realtime database
5. Start in test mode
6. Make not of the database url
7. Using the stacked menu on the right, import the firebase_import.json file from your github repo
8. Click the gear next to Project Overview and select project settings
9. Navigate to the service accounts tab
10. Click generate new private key
11. Use the contents of this file as the values for your config vars in step 8 of Create Heroku Account

### Create Heroku Account
Create a Heroku account at signup.heroku.com. 
1. Click create new app
2. Name your app (e.g. madden-cfm-groupme-bot)
3. Click create app
4. For deployment method select GitHub
5. Click connect to GitHub
6. Search for madden-cfm-chatbot repo and connect
7. Go to the settings tab and reveal config vars
8. Enter values for the following keys: 'FIREBASE_CREDS_TYPE', 'FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL', 'FIREBASE_CLIENT_ID', 'FIREBASE_AUTH_URI', 'FIREBASE_TOKEN_URI', 'FIREBASE_AUTH_PROVIDER', 'FIREBASE_CLIENT_CERT_URL', 'GROUPME_TOKEN', 'GROUPME_GROUP_ID', 'DATABASE_URL'
9. Navigate back to deploy tab and manually deploy the master branch, by clicking the deploy branch button

### Download the Madden 19 Madden Companion App
Connect the Madden Companion App to your application server
1. Navigate to the export tab of your franchise
2. Set the export url (e.g. https://NAME-OF-HEROKU-APP.herokuapp.com/exports)
