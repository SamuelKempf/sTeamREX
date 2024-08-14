import json
import re
import requests as r
from bs4 import BeautifulSoup


def get_game_data(game_data):
    url = f"https://store.steampowered.com/api/appdetails?appids={game_data['appid']}"
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
        return {'title': 'Delisted', 'appid': game_data['appid'], 'playtime': game_data['playtime'], 'release_date': 'N/A', 'genres': 'N/A'}

    if not content:
        print(f"No data available for {game_data['appid']}!")
        return {'title': 'Delisted', 'appid': game_data['appid'], 'playtime': game_data['playtime'], 'release_date': 'N/A', 'genres': 'N/A'}

    json_data = json.loads(content)

    if not json_data[f"{game_data['appid']}"]["success"]:
        return {'title': 'Delisted', 'appid': game_data['appid'], 'playtime': game_data['playtime'], 'release_date': 'N/A', 'genres': 'N/A'}

    title = json_data[f"{game_data['appid']}"]['data']['name']
    release_date = json_data[f"{game_data['appid']}"]['data']['release_date']['date']

    if "genres" in json_data[f'{game_data['appid']}']['data']:
        genres = ""
        genre_list = []
        for genre in json_data[f'{game_data['appid']}']['data']['genres']:
            genre_list.append(genre['description'] + ',')

        for genre in genre_list:
            genres += genre

        genres = genres[:-1]
    else:
        genres = 'none'

    tags = get_tags(game_data['appid'])

    game_info = {'title': title, 'appid': game_data['appid'], 'playtime': game_data['playtime'], 'release_date': release_date, 'genres': genres, 'tags': tags}

    return game_info


def get_users_games(api_key, steam_id):
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&format=json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    myreq = r.get(url, headers=headers)
    content = myreq.content

    return json.loads(content)


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
        print(app_id)
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

    if pos_revs != 0 and neg_revs != 0:
        rev_score = round(pos_revs / (pos_revs + neg_revs), 2)
    elif pos_revs > 0 and neg_revs == 0:
        rev_score = 1
    elif pos_revs == 0 and neg_revs > 0:
        rev_score = 0
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
    return round(rev_score, 2)


def get_steamid(username):
    url = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={apikey}&vanityurl={username}'

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    myreq = r.get(url, headers=headers)
    content = myreq.content

    status_code = myreq.status_code
    reason = myreq.headers
    if status_code != 200:
        print("Error: status code:", status_code, " - ", reason)

    json_data = json.loads(content)

    return json_data['response']['steamid']


def get_tags(appid):
    url = f'https://store.steampowered.com/app/{appid}'
    page = r.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    if soup.find(name='div', id='glanceCtnResponsiveRight') is None:
        return 'none'

    results = soup.find(name='div', id='glanceCtnResponsiveRight').text

    tags = results.replace('Tags', '')
    tags = tags.replace('Popular user-defined tags for this product:', '')
    tags = tags.replace('\t', '')
    tags = tags.replace('\n', '')
    tags = tags.replace('\r', ',')
    tags = tags.split(':', 1)[0]
    tags = tags.replace('ReviewsAll Reviews', '')
    tags = tags.replace('+', '')
    tags = tags[1:]

    return tags


def scrape_reviews(appid):
    url = f'https://store.steampowered.com/app/{appid}'
    page = r.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(name='div', id='userReviews')
    revs = results.find_all("span", class_="nonresponsive_hidden responsive_reviewdesc")

    if len(revs) == 1:
        review_data = revs[0].text
    else:
        review_data = revs[1].text

    pos_perc = review_data
    pos_perc = re.sub(r'[\x00-\x1f]', '', pos_perc)
    pos_perc = "".join(pos_perc.split())
    perc_loc = pos_perc.find('%')
    pos_perc = pos_perc[1:perc_loc]
    pos_perc = '0.' + pos_perc

    total_reviews = review_data
    total_reviews = re.sub(r'[\x00-\x1f]', '', total_reviews)
    total_start = total_reviews.find(' of the ') + 8
    total_end = total_reviews.find(' user reviews')
    total_reviews = total_reviews[total_start:total_end]
    total_reviews = total_reviews.replace(",", "")

    pos_revs = round(int(total_reviews) * float(pos_perc))
    neg_revs = int(total_reviews) - pos_revs
    return pos_revs, neg_revs
