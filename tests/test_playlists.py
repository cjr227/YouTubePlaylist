#!/usr/bin/python

from nose.tools import *
import unittest
import re
import unicodedata
import pandas as pd
import numpy as np
import math
import httplib2
import os
import sys
import prod_playlists as yt

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

CLIENT_SECRETS_FILE = "client_secrets.json"

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

YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class test_create_playlist(unittest.TestCase):
    """Tests creating a playlist

    """

    def setUp(self):
        self.youtube = yt.get_authenticated_service()
        self.play_create = []

    def test_playlist_create(self):
        self.play_create = yt.create_playlist(self.youtube, 0)
        assert self.play_create.keys() == [u'snippet',u'status',u'kind',
                                          u'etag',u'id']

    def test_playlist_add(self):
        videoID = "KP7f5wlSeJk"
        self.play_create = yt.create_playlist(self.youtube, 0)
        playlist_id = self.play_create["id"]
        play_add = yt.add_video_to_playlist(self.youtube, videoID, playlist_id)
        play_search = self.youtube.playlistItems().list(part="snippet", 
                                                        playlistId = playlist_id
                                                        ).execute()
        search_video_id = play_search["items"][0]["snippet"]["resourceId"]["videoId"]
        assert videoID == search_video_id

class test_video_info(unittest.TestCase):
    """Tests retrieval of video information

    """

    def setUp(self):
        self.youtube = yt.get_authenticated_service()
        keyword = "sample keyword"
        self.search_result = yt.youtube_search(self.youtube, keyword, 1)[0]

    def test_is_video(self):
        assert yt.is_video(self.search_result) is True


    def test_retrieve_video_title(self):
        assert yt.retrieve_video_title(self.search_result) == "sample title"


    def test_retrieve_video_user(self):
        assert yt.retrieve_video_user(self.search_result) == "sample user name"


    def test_retrieve_video_description(self):
        assert yt.retrieve_video_description(self.search_result) == "sample video description"


    def test_retrieve_video_id(self):
        assert yt.retrieve_video_id(self.search_result) == "sample video ID"


    def test_retrieve_video_length(self):
        vid_id = yt.retrieve_video_id(self.search_result)
        assert yt.retrieve_video_length(self.youtube, vid_id) == "sample video length"


class test_irrelevance(unittest.TestCase):
    """Tests determination of video relevance based on title info

    """

    def setUp(self):
        self.irrv_list = yt.create_irrv_token_list()

    def test_is_irrelevant(self):
        title = "sample title"
        assert yt.is_irrelevant(title, self.irrv_list) is True


def main():
    unittest.main()

if __name__ == '__main__':
    main()
