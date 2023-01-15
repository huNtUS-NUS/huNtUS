<p align="center">
  <img src="https://user-images.githubusercontent.com/35778042/212503801-6c75b068-c047-4ab0-b88c-efa402d3b0b8.png" />
</p>

## Inspiration
Being a hobbyist in geocaching and wanting to do it in school so it's more convenient. Also wanting to share the fun experiences geocaching can give people!

## What it does
It allows OGLs to scatter geocaches everywhere around the school at places of interest and allows the OGLings to try and find the geocaches in an amazing race!

_Facilitators_
1. **`/start`**
    - Initialises the game in a Telegram group (command executor will be the game master)
2. **`/facil`**
    - Promotes a user to the 'facilitator' role using a password given to the game master
3. **`/create_cache`**
    - Creates a new huNtUS cache by prompting for its details (i.e. name, description, specific location)
4. **`/play`**
    - Begins the gameplay, allowing for players to submit secret codes belonging to huNtUS caches

_Players_
1. **`/join`**
    - Join an existing game
2. **`/submit`**
    - Submit the secret code to capture a huNtUS cache
3. **`/list`**
    - Lists all undiscovered huNtUS caches in the current game
4. **`/view`**
    - View a specific huNtUS cache's details (i.e. name, description, generic location)

## How we built it
We used the python-telegram-bot API and many instances of testing by pressing f5 and control+C during the 24 hours `:     ^)`

## Challenges we ran into
- A bug that took us 1 hour to solve was just because we needed to reply to the message
- Lack of sleep
- The Great NUS Firewall preventing access to MongoDB (we switched to Firebase instead)
- Lack of sleep

## What we learned
Success is not final, failure is not fatal. What is most important is the courage to move on.

## What's next for huNtUS
Making the process more user-friendly and streamlined.
