import json
import os


def append_list(games_db, filename):
    # Check if the file already exists
    if os.path.isfile(filename):
        # Append data to the existing file without writing the header
        games_db.to_csv(filename, mode='a', header=False, index=False)
    else:
        # Write data to a new file with the header
        games_db.to_csv(filename, mode='w', header=True, index=False)


def load_games(steam_id):
    filename = f'{steam_id}_games.json'
    if not os.path.isfile(filename):
        print(f'{filename} does not exist. Run sTeamREX with Update = True.')
        exit()

    with open(filename, encoding='utf-8') as fh:
        return json.load(fh)


def save_list(games_db, filename):
    games_db.to_csv(filename, index=False)

    return True


def save_user_games(games, steam_id):
    filename = f'{steam_id}_games.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(games, f, ensure_ascii=False, indent=4)