import json
import pandas as pd
import re
import requests as r
from bs4 import BeautifulSoup
from collections import OrderedDict
from operator import itemgetter
from pprint import pprint


def sort_dict_by_value(uo_dict):
    sorted_list = sorted(uo_dict.items(), key=itemgetter(1))
    return OrderedDict(sorted_list)


def sort_dict_by_value_reverse(uo_dict):
    sorted_list = sorted(uo_dict.items(), key=itemgetter(1), reverse=True)
    return OrderedDict(sorted_list)


def get_rating(app_id):
    url = f'https://store.steampowered.com/appreviews/{app_id}?json=1'
    headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
    }

    myreq = r.get(url, headers=headers)
    content = myreq.content

    # Check if request was successful
    status_code = myreq.status_code
    reason = myreq.headers
    if status_code != 200:
        print(url)
        print("Error: status code:", status_code, " - ", reason)

    if not content:
        return 1

    json_data = json.loads(content)

    if not json_data["success"]:
        return 1

    try:
        pos_revs = json_data['query_summary']['total_positive']
        neg_revs = json_data['query_summary']['total_negative']
    except KeyError:
        print(f'Error retrieving reviews for appid: {app_id}')
        pos_revs = 0
        neg_revs = 0

    # If both review scores are > 0, calculate the percentage of reviews that are positive.
    if pos_revs != 0 and neg_revs != 0:
        rev_score = int(pos_revs / (pos_revs + neg_revs))
    # If there are positive reviews but no negative reviews, set the review score to 1.
    elif pos_revs > 0 and neg_revs == 0:
        rev_score = 1
    # If there are no positive reviews, only negative reviews, then set the review score to 0.
    elif pos_revs == 0 and neg_revs > 0:
        rev_score = 0
    # If there are no review counts included in the JSON object, then try retrieving the scores by scraping the game's web page.
    else:
        pos_revs, neg_revs = scrape_reviews(app_id)
        if pos_revs != 0 and neg_revs != 0:
            rev_score = int(pos_revs / (pos_revs + neg_revs))
        elif pos_revs > 0 and neg_revs == 0:
            rev_score = 1
        elif pos_revs == 0 and neg_revs > 0:
            rev_score = 0
        else:
            print(f"Could not retrieve ratings for {app_id}")
            rev_score = 0

    return rev_score


def save_list(df, filename):
    df.to_csv(filename, index=False)

    return True


def scrape_reviews(appid):
    url = f'https://store.steampowered.com/app/{appid}'
    page = r.get(url)

    soup = bs(page.content, "html.parser")
    results = soup.find(name='div', id='userReviews')
    review = results.find_all("span", class_="responsive_hidden")

    pos_perc = review[0].text
    total_reviews = review[1].text

    pos_perc = re.sub(r'[\x00-\x1f]', '', pos_perc)  # Delete special characters from text.
    pos_perc = pos_perc[1:len(pos_perc) - 1]  # Extract the positive review percentage from text.
    pos_perc = '0.' + pos_perc

    total_reviews = re.sub(r'[\x00-\x1f]', '', total_reviews)  # Delete special characters from the text.
    total_reviews = total_reviews[1:len(total_reviews) - 1]  # Extract the positive review percentage from text.
    total_reviews = total_reviews.replace(",", "")  # Remove any commas from the total.

    pos_revs = int(int(total_reviews) * float(pos_perc))
    neg_revs = int(total_reviews) - pos_revs

    return pos_revs, neg_revs


bs = BeautifulSoup
games_db = pd.read_csv('76561198025848008_games.csv')
games_db.reset_index()
genre_dict = {}
tags_dict = {}

for index, row in games_db.iterrows():
    genres = row['genres']
    genre_list = genres.split(",")  # Separate genre field into a list of genres

    for genre in genre_list:
        if genre == 'none':
            continue

        if genre not in genre_dict.keys():
            if row['playtime'] > 30:
                genre_dict[genre] = [1, 0]
            else:
                genre_dict[genre] = [0, 1]
        else:
            if row['playtime'] > 30:
                genre_dict[genre][0] += 1
            else:
                genre_dict[genre][1] += 1

    tags = row['tags']
    tag_list = tags.split(",")

    for tag in tag_list:
        if tag == 'none':
            continue

        if tag not in tags_dict.keys():
            if row['playtime'] > 30:
                tags_dict[tag] = [1, 0]
            else:
                tags_dict[tag] = [0, 1]
        else:
            if row['playtime'] > 0:
                tags_dict[tag][0] += 1
            else:
                tags_dict[tag][1] += 1

top_genres = ""
top_tags = ""

for keys, value in dict(sorted(genre_dict.items(), key=lambda x: x[1][0], reverse=True)[:5]).items():
    top_genres = top_genres + keys + "\n"

for keys, value in dict(sorted(tags_dict.items(), key=lambda x: x[1][0], reverse=True)[:5]).items():
    top_tags = top_tags + keys + "\n"

mp_genre_dict = {}
mp_tags_dict = {}
mp_games = games_db.nlargest(20, "playtime")


for index, row in mp_games.iterrows():
    genres = row['genres']
    mp_genre_list = genres.split(",")

    for genre in mp_genre_list:
        if genre == 'none':
            continue

        if genre not in mp_genre_dict.keys():
            mp_genre_dict[genre] = [1]
        else:
            mp_genre_dict[genre][0] += 1

    tags = row['tags']
    mp_tags_list = tags.split(",")

    for tag in mp_tags_list:

        if tag == 'none':
            continue

        if tag not in mp_tags_dict.keys():
            mp_tags_dict[tag] = [1]
        else:
            mp_tags_dict[tag][0] += 1

unplayed_db = games_db[games_db['playtime'] <= 30]
unplayed_scores = {}

for index, row in unplayed_db.iterrows():
    genres = row['genres']
    genre_list = genres.split(",")

    for genre in genre_list:
        if row['appid'] not in unplayed_scores:
            unplayed_scores[row['appid']] = 0

        if genre in mp_genre_dict:
            unplayed_scores[row['appid']] += mp_genre_dict[genre][0]

    tags = row['tags']
    tags_list = tags.split(",")

    for tag in tags_list:
        if row['appid'] not in unplayed_scores:
            unplayed_scores[row['appid']] = 0

        if tag in mp_tags_dict:
            unplayed_scores[row['appid']] += mp_tags_dict[tag][0]

for keys, value in unplayed_scores.items():
    rating = get_rating(keys)
    new_score = unplayed_scores[keys] * rating
    unplayed_scores[keys] = new_score

unplayed_scores = sort_dict_by_value_reverse(unplayed_scores)
unplayed_scores = dict(list(unplayed_scores.items())[0: 20])
unplayed_scores = sort_dict_by_value_reverse(unplayed_scores)

recommendations = {}

for keys, value in unplayed_scores.items():
    mask = games_db['appid'] == keys
    title = games_db[mask]['title'].values[0]
    print(title)
    recommendations[title] = value

recommendations = sort_dict_by_value_reverse(recommendations)

pprint(f'The top recommendations from your backlog are: {recommendations}')
