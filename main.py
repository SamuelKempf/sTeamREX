import file_functions as ff
import os
import pandas as pd
import steam_api as api
import time
from collections import OrderedDict
from dotenv import load_dotenv
from operator import itemgetter


def main():
    load_dotenv()
    api_key = os.getenv('API_KEY')
    steam_id = os.getenv('STEAM_ID')
    update = True  # Set to false if the user's games JSON file is up-to-date.
    skip_to_ratings = False  # If the script successfully assembles the games list but crashes on the scoring, this setting allows you to avoid downloading redundant data.

    # Create empty dataframe to store game info
    headers = {'title': ['title'], 'appid': ['appid'], 'playtime': ['playtime'], 'release_date': ['release_date'], 'genres': ['genres'], 'tags': ['tags']}
    games_df = pd.DataFrame(headers)
    games_df = games_df.drop(0)

    if not skip_to_ratings:
        # Load games from exiting JSON file or retrieve them from the Steam API
        if update:
            games = api.get_users_games(api_key, steam_id)
            ff.save_user_games(games, steam_id)
        else:
            games = ff.load_games(steam_id)

        count = 0
        current_game = 0

        filename = f'{steam_id}_games.csv'

        for game in games['response']['games']:
            current_game += 1
            total_games = len(games['response']['games'])

            # Initiate a cooldown period after 100 games to avoid exceeding Steam's API call limit
            if count > 100:
                ff.append_list(games_df, filename)
                print(f"API Rest Initiated. {current_game} of {total_games} have been processed.")
                time.sleep(150)
                count = 0

            game_data = {
                'appid': game['appid'],
                'playtime': game['playtime_forever'],
            }
            games_df.loc[len(games_df)] = api.get_game_data(game_data)

            count += 1

        # Remove delisted games from the dataset and save them in a separate file.
        games_df = sort_delisted(games_df, steam_id)

        filename = f'{steam_id}_games.csv'

        if ff.save_list(games_df, filename):
            print(f'Data saved for {len(games_df)} games.')

    if skip_to_ratings:
        filename = f'{steam_id}_games.csv'
        games_df = pd.read_csv(filename)

    # Check if play time is available. Play time can be set to private even if the games list is public.
    if games_df['playtime'].mean() == 0:
        print(f'{steam_id} has set their play time to be private, thus no recommendations can be made.')
        exit()

    # Determine the number of games to use for ratings based on the size of the user's library.
    if len(games_df) < 100:
        mp_games = games_df.nlargest(5, "playtime")
    elif 100 <= len(games_df) < 250:
        mp_games = games_df.nlargest(10, "playtime")
    elif 250 <= len(games_df) < 500:
        mp_games = games_df.nlargest(15, "playtime")
    elif 500 <= len(games_df) < 1000:
        mp_games = games_df.nlargest(20, "playtime")
    elif 1000 <= len(games_df):
        mp_games = games_df.nlargest(25, "playtime")
    else:
        mp_games = games_df.nlargest(10, "playtime")

    mp_genres = {}
    mp_tags = {}

    # Iterate through the 20 games with the most playtime.
    for index, row in mp_games.iterrows():
        genres = row['genres']
        genre_list = genres.split(",")

        # Compile a collection of all genres assigned to the most played games, along with the number of associated games.
        for genre in genre_list:
            if genre == 'none':
                continue

            if genre not in mp_genres.keys():
                mp_genres[genre] = 1
            else:
                mp_genres[genre] += 1

        tags = row['tags']
        tag_list = tags.split(",")

        # Compile a collection of all tags assigned to the most played games, along with the number of associated games.
        for tag in tag_list:
            if tag == 'none':
                continue

            if tag not in mp_tags.keys():
                mp_tags[tag] = 1
            else:
                mp_tags[tag] += 1

    genres_sorted = sorted(mp_genres.items(), key=itemgetter(1), reverse=True)  # Sort genres by count, descending.
    high_genre_score = int(genres_sorted[0][1])  # The score of the most played genre.
    low_genre_score = genres_sorted[len(genres_sorted) - 1][1]  # The score of the least played genre (of the games played the longest.)
    mid_genre_score = (high_genre_score - low_genre_score) / 2  # The halfway point between the highest and lowest scoring genres.

    genres1 = []  # genres of the most played games
    genres2 = []  # genres of games between the highest and midpoint of the playtime spectrum
    genres3 = []  # genres of games between the midpoint and lowest point of the playtime spectrum
    genres4 = []  # genres of the 20th most played games

    for genre in genres_sorted:
        if genre[1] == high_genre_score:
            genres1.append(genre[0])
        elif mid_genre_score <= genre[1] < high_genre_score:
            genres2.append(genre[0])
        elif mid_genre_score > genre[1] > low_genre_score:
            genres3.append(genre[0])
        else:
            genres4.append(genre[0])

    tags_sorted = sorted(mp_tags.items(), key=itemgetter(1), reverse=True)  # Sort tags by count, descending.
    high_tag_score = int(tags_sorted[0][1])  # The score of the most played tag.
    low_tag_score = int(tags_sorted[len(tags_sorted) - 1][1])  # The score of the least played tag (of the games played the longest.)
    mid_tag_score = (high_tag_score - low_tag_score) / 2  # The halfway point between the highest and lowest scoring tags.

    tags1 = []  # tags of the most played games
    tags2 = []  # tags of games between the highest and midpoint of the playtime spectrum
    tags3 = []  # tags of games between the midpoint and lowest point of the playtime spectrum
    tags4 = []  # tags of the 20th most played games

    for tag in tags_sorted:
        if tag[1] == high_tag_score:
            tags1.append(tag[0])
        elif mid_tag_score <= tag[1] < high_tag_score:
            tags2.append(tag[0])
        elif mid_tag_score > tag[1] > low_tag_score:
            tags3.append(tag[0])
        else:
            tags4.append(tag[0])

    # Compile a dataframe of all games with less than 30 minutes of playtime
    unplayed_df = games_df[games_df['playtime'] <= 30]
    unplayed_scores = {}

    # Iterate through the dataframe of unplayed games, determining the recommendation score based on genres & tags.
    for index, row in unplayed_df.iterrows():
        title = row['title']
        appid = row['appid']
        if title not in unplayed_scores:
            unplayed_scores[title] = 0

        genres = row['genres']
        genre_list = genres.split(",")

        for genre in genre_list:
            if genre in genres1:
                unplayed_scores[title] += 4
            elif genre in genres2:
                unplayed_scores[title] += 3
            elif genre in genres3:
                unplayed_scores[title] += 2
            elif genre in genres4:
                unplayed_scores[title] += 1

        tags = row['tags']
        tag_list = tags.split(",")

        for tag in tag_list:
            if tag in tags1:
                unplayed_scores[title] += 4
            elif tag in tags2:
                unplayed_scores[title] += 3
            elif tag in tags3:
                unplayed_scores[title] += 2
            elif tag in tags4:
                unplayed_scores[title] += 1

        # Obtain the review score from Steam
        rev_score = api.get_rating(appid)

        # Determine the final score by multiplying the genre & tags combined score by the % of positive reviews on Steam.
        unplayed_scores[title] = unplayed_scores[title] * rev_score

    recommendations = sort_dict_by_value_reverse(unplayed_scores)
    recs_df = pd.DataFrame({'name': recommendations.keys(), 'value': recommendations.values()})
    recs_filename = steam_id + "_recs.csv"
    if ff.save_list(recs_df, recs_filename):
        print('Recommendations saved.')
    else:
        print('Something went wrong.')


def sort_delisted(games_df, steam_id):
    delisted_df = games_df.loc[games_df['title'] == 'Delisted']
    ff.save_list(delisted_df, f'{steam_id}_delisted.csv')

    games_df = games_df.loc[games_df['title'] != 'Delisted']
    print(f'{len(delisted_df)} of your games have been delisted.')

    return games_df


def sort_dict_by_value(uo_dict):
    sorted_list = sorted(uo_dict.items(), key=itemgetter(1))
    return OrderedDict(sorted_list)


def sort_dict_by_value_reverse(uo_dict):
    sorted_list = sorted(uo_dict.items(), key=itemgetter(1), reverse=True)
    return OrderedDict(sorted_list)


main()
