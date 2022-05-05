This repository contains the complete application


## Cloning

### Step 1 : cloning the whole project
Use ```git clone https://github.com/SMART-4IF/WebApp.git``` to clone the whole project

### Step 2 : cloning the grammar module
Go to the ```WebApp/streamApp/``` folder
Use ```git clone https://github.com/SMART-4IF/Grammar.git``` to clone the grammar module in the ```WebApp/streamApp/Grammar``` folder

### Install the requirements 
Use ```pip install -r requirements.txt``` to install all the python packages needed



## SpeechToText
To use the SpeechToText functionality of the application, you need to setup an environment variable called GOOGLE_APPLICATION_CREDENTIALS whose value is the path of a Google's service account key.
This key is a .json file.
Once this environment variable set, restart your computer.



## Running the app

### Running redis
You need to have docker installed and use this command : ```docker run -p 6379:6379 -d redis:5```

### Running django
To run the django server, go to ```WebApp/``` folder and use this command : ```python .\manage.py runserver```. It should start at the address ```127.0.0.1:8000```

## Testing the video
Go to ```https://ngrock.com/download``` and follow the given instructions. Be careful, you need to use the port ```8000``` instead of ```80``` for the last command.
Then, send the link to other users. Be careful, they need to be connected to same network as yours.

## References and tutorials:

1. https://www.youtube.com/watch?v=MBOlZMLaQ8g
2. https://webrtc.org/getting-started/peer-connections
3. https://channels.readthedocs.io/en/stable/tutorial/part_2.html
4. https://www.youtube.com/watch?v=DvlyzDZDEq4
5. https://github.com/WebDevSimplified/Zoom-Clone-With-WebRTC/tree/master/public
6. https://learndjango.com/tutorials/django-signup-tutorial
7. https://docs.djangoproject.com/fr/2.2/topics/auth/default/#:~:text=To%20change%20a%20user's%20password,password%20will%20be%20changed%20immediately.
8. https://stackabuse.com/working-with-redis-in-python-with-django/
9. https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id
