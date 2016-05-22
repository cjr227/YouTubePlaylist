#!/usr/bin/python

import re
import unicodedata
import pandas as pd
import numpy as np
import math
import httplib2
import os
import sys

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


def search_videos(youtube, keyword, artist, song, maxResults=5):
    import re
    artist = artist.lower()
    song = song.lower()
    artist_sub = re.sub("[^\w\s]", "", artist)
    song_sub = re.sub("[^\w\s]", "", song)
    artist_and = re.sub("&", "and", artist)
    song_and = re.sub("&", "and", song)
    # Check for matches with punctuation/symbols and without

    response = youtube.search().list(q=keyword,
                                     part="id,snippet",
                                     maxResults=maxResults
                                     ).execute().get("items", [])

    videos = []

    for record in response:
        if record["id"]["kind"] == "youtube#video":
            title = record["snippet"]["title"].encode(encoding='UTF-8',
                                                      errors='strict').lower()
            user = record["snippet"]["channelTitle"].encode(encoding='UTF-8',
                                                            errors='strict').lower()
            description = record["snippet"]["description"].encode(
                encoding='UTF-8', errors='strict').lower()
            youtube_id = record["id"]["videoId"].encode(encoding='UTF-8',
                                                        errors='strict')
            # Call videos.list method to retrieve location details for video.
            video_response = youtube.videos().list(
                id=youtube_id,
                part='contentDetails'
            ).execute()
            length = video_response.get("items", [])[0][
                "contentDetails"]["duration"]
            length = length.encode(encoding='UTF-8', errors='strict').lower()
            user_search = re.search("band|official|VEVO|records", user,
                                    flags=re.IGNORECASE)
            minute_search = re.search("pt([0-9]{1,}h)?([0-9]{1,2})m([0-9]{1,2})s",
                                      length, flags=re.IGNORECASE)
            if ("rehearsal" not in title and "h" not in length and
                    minute_search is not None):
                # If the song is less than an hour and is not a rehearsal
                if int(minute_search.group(2)) <= 20:
                    # If the song is less than 20 minutes
                    if ((artist in description or artist_sub in description or
                         artist_and in description) and
                            (song in title or song_sub in title or song_and in title) and
                            "provided to youtube" in description):
                        # If song comes from an auto-generated channel by
                        # YouTube
                        videos.append({
                            'youtube_id': youtube_id,
                            'title': title,
                            'priority_flag': 1
                        })
                    elif user_search is not None or user in [artist, artist_sub, artist_and]:
                        # If the song comes from an official channel by the
                        # band/label
                        if ((artist in title and song in title) or
                                (artist_sub in title and song_sub in title) or
                                (artist_and in title and song_and in title)):
                            videos.append({
                                'youtube_id': youtube_id,
                                'title': title,
                                'priority_flag': 2
                            })
                    elif ((artist in title and song in title) or
                          (artist_sub in title and song_sub in title) or
                          (artist_and in title and song_and in title)):
                        # If the song comes from an unofficial channel
                        videos.append({
                            'youtube_id': youtube_id,
                            'title': title,
                            'priority_flag': 3
                        })
    try:
        PriorityCheck = [d['priority_flag'] == 1 for d in videos]
        return videos[PriorityCheck.index(True)]
    except ValueError:
        try:
            PriorityCheck = [d['priority_flag'] == 2 for d in videos]
            return videos[PriorityCheck.index(True)]
        except ValueError:
            try:
                PriorityCheck = [d['priority_flag'] == 3 for d in videos]
                return videos[PriorityCheck.index(True)]
            except ValueError:
                return "No results found"


def add_video_to_playlist(youtube, videoID, playlistID):
    add_video_request = youtube.playlistItems().insert(
        part="snippet",
        body={
            'snippet': {
                'playlistId': playlistID,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': videoID
                }
                #'position': 0
            }
        }
    ).execute()


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

if __name__ == '__main__':
    NewSongs = pd.read_csv(r'SongsToAdd.csv')
    TotalSongs = np.shape(NewSongs)[0]
    MaxVideos = 200
    # Maximum number of videos per playlist
    TotalPlaylists = int(math.ceil(1. * TotalSongs / MaxVideos))
    AddedSongs = []
    # List that contains the songs that were successfully added to a playlist

    youtube = get_authenticated_service()
    inner_loop_index = 0
    for i in range(TotalPlaylists):
        # This code creates a new, public playlist in the authorized user's
        # channel.
        playlists_insert_response = youtube.playlists().insert(
            part="snippet,status",
            body=dict(
                snippet=dict(
                    title="Playlist %d v2" % i,
                    description="A music playlist created with the YouTube API v3"
                ),
                status=dict(
                    privacyStatus="public"
                )
            )
        ).execute()
        playlist_id = playlists_insert_response["id"]
        for j in range(0, MaxVideos):
            try:
                if j + inner_loop_index == TotalSongs:
                    break
                artist = NewSongs.loc[
                    j + inner_loop_index, ["Artist"]].values[0]
                song = NewSongs.loc[j + inner_loop_index, ["Song"]].values[0]
                results = search_videos(
                    youtube, artist + ' ' + song, artist, song, maxResults=5)
                if results != "No results found":
                    add_video_to_playlist(
                        youtube, results['youtube_id'], playlist_id)
                    AddedSongs.append(
                        NewSongs.loc[j + inner_loop_index, ["ID"]].values[0])
            except HttpError, e:
                MissedSongs = NewSongs[~NewSongs["ID"].isin(AddedSongs)]
                MissedSongs.to_csv(path_or_buf="MissedSongs_%d_%d.csv" %
                                   (i, inner_loop_index), index=False)
                print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
        inner_loop_index += MaxVideos
    MissedSongs = NewSongs[~NewSongs["ID"].isin(AddedSongs)]
    MissedSongs.to_csv(path_or_buf="MissedSongs_Final.csv", index=False)
