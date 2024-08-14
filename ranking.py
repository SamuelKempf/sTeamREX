import file_functions as ff
import os
import pandas as pd
import steam_api as api
from dotenv import load_dotenv
from collections import OrderedDict
from operator import itemgetter


def main():
    filename = steam_id + '_games.csv'
    games_df = pd.read_csv(filename)
    games_df.reset_index()
    mp_games = games_df.nlargest(20, "playtime")
    mp_genres = {}
    mp_tags = {}

    # Iterate through the top 20 games with the most playtime.
    for index, row in mp_games.iterrows():
        genres = row['genres']
        genre_list = genres.split(",")

        # Compile a list of all genres assigned to the most played games, along with the number of associated games.
        for genre in genre_list:
            if genre == 'none':
                continue

            if genre not in mp_genres.keys():
                mp_genres[genre] = 1
            else:
                mp_genres[genre] += 1

        tags = row['tags']
        tag_list = tags.split(",")

        # Compile a list of all tags assigned to the most played games, along with the number of associated games.
        for tag in tag_list:
            if tag == 'none':
                continue

            if tag not in mp_tags.keys():
                mp_tags[tag] = 1
            else:
                mp_tags[tag] += 1

    genres_sorted = sorted(mp_genres.items(), key=itemgetter(1), reverse=True)
    high_genre_score = int(genres_sorted[0][1])
    low_genre_score = genres_sorted[len(genres_sorted) - 1][1]
    mid_genre_score = (high_genre_score - low_genre_score) / 2

    genres1 = []
    genres2 = []
    genres3 = []
    genres4 = []

    for genre in genres_sorted:
        if genre[1] == high_genre_score:
            genres1.append(genre[0])
        elif mid_genre_score <= genre[1] < high_genre_score:
            genres2.append(genre[0])
        elif mid_genre_score > genre[1] > low_genre_score:
            genres3.append(genre[0])
        else:
            genres4.append(genre[0])

    unplayed_df = games_df[games_df['playtime'] <= 30]
    unplayed_scores = {}

    tags_sorted = sorted(mp_tags.items(), key=itemgetter(1), reverse=True)
    high_tag_score = int(tags_sorted[0][1])
    low_tag_score = int(tags_sorted[len(tags_sorted) - 1][1])
    mid_tag_score = (high_tag_score - low_tag_score) / 2

    tags1 = []
    tags2 = []
    tags3 = []
    tags4 = []

    for tag in tags_sorted:
        if tag[1] == high_tag_score:
            tags1.append(tag[0])
        elif mid_tag_score <= tag[1] < high_tag_score:
            tags2.append(tag[0])
        elif mid_tag_score > tag[1] > low_tag_score:
            tags3.append(tag[0])
        else:
            tags4.append(tag[0])

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

        rev_score = api.get_rating(appid)

        unplayed_scores[title] = unplayed_scores[title] * rev_score

    recommendations = sort_dict_by_value_reverse(unplayed_scores)
    recs_df = pd.DataFrame({'name': recommendations.keys(), 'value': recommendations.values()})
    recs_filename = steam_id + "_recs_upper.csv"
    if ff.save_list(recs_df, recs_filename):
        print('Recommendations saved.')
    else:
        print('Something went wrong.')


def sort_dict_by_value(uo_dict):
    sorted_list = sorted(uo_dict.items(), key=itemgetter(1))
    return OrderedDict(sorted_list)


def sort_dict_by_value_reverse(uo_dict):
    sorted_list = sorted(uo_dict.items(), key=itemgetter(1), reverse=True)
    return OrderedDict(sorted_list)


load_dotenv()
api_key = os.getenv('API_KEY')
steam_id = os.getenv('STEAM_ID')
main()
