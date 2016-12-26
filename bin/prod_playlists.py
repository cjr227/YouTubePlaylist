#!/usr/bin/python

import re
import unicodedata
import pandas as pd
import math
import httplib2
import os
import sys
import argparse

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0
To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the Developers Console
https://console.developers.google.com/
For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flags = argparser.parse_args()
        credentials = run_flow(flow, storage, flags)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def name_variations(name):
    """Computes variations of string with punctuation/symbols and without
    """
    name = name.lower()
    name_sub = re.sub("[^\w\s]", "", name)
    name_and = re.sub("&", "and", name)
    return [name, name_sub, name_and]


def youtube_search(youtube, keyword, maxResults):
    """Retrieve list of results for video search
    """
    return youtube.search().list(q=keyword,
                                 part="id,snippet",
                                 maxResults=maxResults
                                 ).execute().get("items", [])


def is_video(search_result):
    """Check if YouTube search result is a video
    """
    if search_result["id"]["kind"] == "youtube#video":
        return True
    else:
        return False


def retrieve_video_title(search_result):
    """Store title of YouTube video
    """
    title = search_result["snippet"]["title"]
    title = title.encode(encoding='UTF-8', errors='strict')
    title = title.lower()
    return title


def retrieve_video_user(search_result):
    """Store user of YouTube video
    """
    user = search_result["snippet"]["channelTitle"]
    user = user.encode(encoding='UTF-8', errors='strict')
    user = user.lower()
    return user


def retrieve_video_description(search_result):
    """Store description of YouTube video
    """
    description = search_result["snippet"]["description"]
    description = description.encode(encoding='UTF-8', errors='strict')
    description = description.lower()
    return description


def retrieve_video_id(search_result):
    """Store ID of YouTube video
    """
    youtube_id = search_result["id"]["videoId"]
    youtube_id = youtube_id.encode(encoding='UTF-8', errors='strict')
    return youtube_id


def retrieve_video_length(youtube, youtube_id):
    """Retrieve duration info for specific video
    """
    video_response = youtube.videos().list(
        id=youtube_id,
        part='contentDetails'
    ).execute()

    length = video_response.get("items", [])[0][
        "contentDetails"]["duration"]
    length = length.encode(encoding='UTF-8', errors='strict').lower()
    return length


def parse_video_length(length):
    """Retrieve number of hours, minutes, and seconds for specific video
    """
    len_search = re.search("pt([0-9]{1,}h)?([0-9]{1,2})m([0-9]{1,2})s",
                           length, flags=re.IGNORECASE)
    if len_search is not None:
        return [len_search.group(1), len_search.group(2), len_search.group(3)]
    else:
        return None


def create_irrv_token_list():
    """Create list of regex for irrelevant videos
    """
    irrv_list = []
    irrv_list.append("rehearsal")
    irrv_list.append("behind the scenes")
    irrv_list.append("(guitar|drum|bass) (cover|playthrough|tab)")
    irrv_list.append("\((live|cover)\)$")
    return irrv_list


def is_irrelevant(title, irrv_list):
    """Check if video title contains terms that render video irrelevant
    """
    for token in irrv_list:
        title_search = re.search(token, title, flags=re.IGNORECASE)
        if title_search is not None:
            return True
        else:
            continue
    return False


def official_channel_search(user):
    """Search channel title for indicators of being an official channel
    """
    user_search = re.search("band|official|VEVO|records", user,
                            flags=re.IGNORECASE)
    return user_search


def is_official_channel(user, user_search, artist_variations):
    """Check if a video comes from an official channel by the artist/label
    """
    if user_search is not None or user in artist_variations:
        return True
    else:
        return False


def name_fuzzy_match(variations, search_text):
    """Check if string variations of a name appear in search text
    """
    return any(x in search_text for x in variations)


def is_auto_channel(artist_variations, song_variations, title, description):
    """Check if video comes from auto-generated channel by YouTube
    """
    if (name_fuzzy_match(artist_variations, description) and
        name_fuzzy_match(song_variations, title) and
            "provided to youtube" in description):
        return True
    else:
        return False


def search_videos(youtube, artist, song, maxResults, irrv_list):
    """Search for top relevant videos given keyword
    """
    artist_variations = name_variations(artist)
    song_variations = name_variations(song)
    keyword = artist + ' ' + song
    response = youtube_search(youtube, keyword, maxResults)
    videos = []

    for record in response:
        if is_video(record):
            title = retrieve_video_title(record)
            user = retrieve_video_user(record)
            description = retrieve_video_description(record)
            youtube_id = retrieve_video_id(record)
            length = retrieve_video_length(youtube, youtube_id)
            user_search = official_channel_search(user)
            length_search = parse_video_length(length)
            artist_title_match = name_fuzzy_match(artist_variations, title)
            song_title_match = name_fuzzy_match(song_variations, title)
            if (not is_irrelevant(title, irrv_list) and
                    length_search is not None):
                # If video does not contain terms irrelevant to search
                hours, minutes, seconds = [length_search[0],
                                           int(length_search[1]),
                                           int(length_search[2])]
                if minutes <= 20 and hours is None:
                    # If video is less than 20 minutes
                    if is_auto_channel(artist_variations, song_variations,
                                       title, description):
                        videos.append({
                            'youtube_id': youtube_id,
                            'title': title,
                            'priority_flag': 1
                        })
                    elif is_official_channel(user, user_search, artist_variations):
                        # If the song comes from an official channel by the
                        # band/label
                        if (artist_title_match and song_title_match):
                            videos.append({
                                'youtube_id': youtube_id,
                                'title': title,
                                'priority_flag': 2
                            })
                    elif (artist_title_match and song_title_match):
                        # If the song comes from an unofficial channel
                        videos.append({
                            'youtube_id': youtube_id,
                            'title': title,
                            'priority_flag': 3
                        })
    return videos


def retrieve_top_video(videos):
    """Returns most relevant video for given search term
    """
    for i in range(1, 4):
        try:
            PriorityCheck = [d['priority_flag'] == i for d in videos]
            return videos[PriorityCheck.index(True)]
        except ValueError:
            if i < 3:
                continue
            else:
                return "No results found"


def create_playlist(youtube, val):
    """Creates a new, public playlist in the authorized user's channel
    """
    playlists_insert_request = youtube.playlists().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
                title="Playlist %d v3" % val,
                description="A music playlist created with the YouTube API v3"
            ),
            status=dict(
                privacyStatus="public"
            )
        )
    ).execute()
    return playlists_insert_request


def add_video_to_playlist(youtube, videoID, playlistID):
    """Adds specified video to given playlist
    """
    add_video_request = youtube.playlistItems().insert(
        part="snippet",
        body={
            'snippet': {
                'playlistId': playlistID,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': videoID
                }
            }
        }
    ).execute()

def quota_estimate(TotalPlaylists, TotalSongs):
    """Estimates current quota usage
    """
    playlist_create_cost = 50*TotalPlaylists
    playlist_insert_cost = 50*TotalSongs
    video_search_cost = 100*TotalSongs
    video_info_cost = 3*TotalSongs
    total_cost = (playlist_create_cost + playlist_insert_cost +
    video_search_cost + video_info_cost)
    return total_cost

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    NewSongs = pd.read_csv(args.filename)
    TotalSongs = len(NewSongs)
    MaxVideos = 200
    # Maximum number of videos per playlist
    TotalPlaylists = int(math.ceil(1. * TotalSongs / MaxVideos))
    AddedSongs = []
    # Contains songs that were successfully added to a playlist
    est = quota_estimate(TotalPlaylists, TotalSongs)
    if est >= 1000000:
        print """WARNING: Your quota usage is estimated to exceed your daily limit.
        Please proceed accordingly."""
        sys.exit()
    print """NOTE: Your estimated quota usage is %i units.""" % est
    youtube = get_authenticated_service()
    song_index = 0
    irrv_list = create_irrv_token_list()
    for i in range(TotalPlaylists):
        playlists_insert_response = create_playlist(youtube, i)
        playlist_id = playlists_insert_response["id"]
        for j in range(0, MaxVideos):
            try:
                if j + song_index == TotalSongs:
                    break
                artist = NewSongs.loc[
                    j + song_index, ["Artist"]].values[0]
                song = NewSongs.loc[j + song_index, ["Song"]].values[0]
                videos = search_videos(
                    youtube, artist, song, maxResults=5, irrv_list=irrv_list)
                top_vid = retrieve_top_video(videos)
                if top_vid != "No results found":
                    add_video_to_playlist(
                        youtube, top_vid['youtube_id'], playlist_id)
                    AddedSongs.append(
                        NewSongs.loc[j + song_index, ["ID"]].values[0])
            except HttpError, e:
                MissedSongs = NewSongs[~NewSongs["ID"].isin(AddedSongs)]
                MissedSongs.to_csv(path_or_buf="MissedSongs_%d_%d.csv" %
                                   (i, song_index), index=False)
                print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
        song_index += MaxVideos
    MissedSongs = NewSongs[~NewSongs["ID"].isin(AddedSongs)]
    MissedSongs.to_csv(path_or_buf="MissedSongs_Final.csv", index=False)

if __name__ == '__main__':
    main()
