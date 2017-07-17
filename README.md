# YouTubePlaylist
Feed list of songs into playlists on YouTube!

If you have a specific list of songs that you would like to add to one or more YouTube playlists, then this script can search for them and add them to playlists on your YouTube channel.

This project assumes that you have a Google Developers account, and a project that has access to the YouTube Data API with OAuth 2.0 authorization. All restrictions apply.

Credit for inspiration goes to the [Python code samples for the YouTube Data API](https://github.com/youtube/api-samples/tree/master/python).

## Setup

1. Save a CSV file of artist names and song titles in the following format.

    | ID | Artist     | Song                  |
    |----|------------|-----------------------|
    | 1  | Pink Floyd | Goodbye Blue Sky      |
    | 2  | Sean Paul  | Like Glue             |
    | 3  | The O'Jays | For the Love of Money |

2. On the Google Developers site, follow [these](https://developers.google.com/youtube/v3/getting-started) instructions for setting up an account.
3. Under the [Developers Console](https://console.developers.google.com/), select your project and click "Credentials". 
4. Save your OAuth2 credentials as "client_secrets.json".
5. Pull the latest copy of this repository.

    ```
    git pull https://github.com/cmeb45/YouTubePlaylist
    ```

6. Save your credentials file and the file of songs in the same directory as the main script file "prod_playlists.py".
7. Execute the script as follows, where *filename* is the CSV file of songs.

    ```
    python prod_playlists.py filename
    ``` 

Any songs that have not been successfully added to a playlist on your account will be saved in an error file.
