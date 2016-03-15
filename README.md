# YouTubePlaylist
Feed list of songs into playlists on YouTube!

If you have a specific list of songs that you would like to add to one or more YouTube playlists, then this script can search for them and add them to playlists on your YouTube channel.

This project assumes that you have a Google Developers account, and a project that has access to the YouTube Data API. All restrictions apply.

This work is still in beta testing. Under version 1, I searched for 1,161 songs, the vast majority of which were hard rock and heavy metal (with a few exceptions of rap/hip-hop, funk, disco, and other miscellaneous genres!). 
- 1,017 (87.7%) were correctly discovered and added to my playlists.
- 87 (7.5%) were not found
  - 17 of which due to an ampersand (&) that appeared in place of the word "AND" in the song title
  - 5 of which had a non-ASCII character in the song title.
- 57 (4.8%) incorrect videos were added
  - 38 of which were live videos of artist performances
  - 10 of which were covers (vocal/guitar/drum/bass, etc.)
  - 5 of which were incorrect songs
  - 4 of which were other versions of those songs (remixes/acoustic/unplugged, etc.)

For version 2, I searched for 1,202 songs, revising the logic to allow for matching on either an ampersand or its equivalent "AND".
- 1,074 (89.3%) were correctly discovered and added to my playlists.
- 67 (5.6%) were not found
  - 5 of which had a non-ASCII character in the song title
- 61 (5.1%) incorrect videos were added
  - 40 of which were live videos of artist performances
  - 12 of which were covers (vocal/guitar/drum/bass, etc.)
  - 5 of which were incorrect songs
  - 4 of which were other versions of those songs (remixes/acoustic/unplugged, etc.)

For version 3, I will work to ensure that as many covers and live versions are ignored from consideration. 

There are also future plans to have a larger training corpus so that songs of other genres are more represented and can be added to playlists. 
