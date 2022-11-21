# Kanban Application

## Functionality

Simple Kanban
This Application Helps in Our Work Management and tracking of Todo Tasks


Board
It's a board that resemble a physical board that can have many tasks lists and cards under that

Lists
Lists are under a board they are represented as a vertical list of cards

Cards
Each card is a task. A card belongs to one List. Cards can be moved from one list to another. it can also be moved as completed.

## File Structure

The root directory contains the following files:

- `requirements.txt` contains the required packages for the project.
  
- `app.py` gets the app to run and where all the codes are written.
- 
- `documentaion` is a folder which contains documented API file that is KanbanApi.yaml and raw documentaion file that is kanbanApi_raw.txt
 
- `docs/` is a folder which contains ProjectReport and video link file regarding Project Work

- `templates/` is a folder which contains html templates to be rendered.

`tododb.db` is a file which contain sqlite database models


## To Run The Code

open `Terminal` and type :-  

```
python -m venv env

```
This will create and set up the virtual environment.
Once the `virtual Environment` setup now we need to `install` all the requirements packages from `requirements.txt` to virtual environment `env`:-

In the `Terminal` type:-
```

.\\\env\Scripts\activate
```

This will `config` the Interpreter with Virtual Environment

Now Install the requirents by typing in `terminal` :-
```

pip install -r requirements.txt
```
After `Installation Complete` just run this code in terminal:-
```
python app.py
```


` This is based on [MAD_1 Project].  `


