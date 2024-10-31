import os

from dotenv import load_dotenv
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from functools import lru_cache

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@lru_cache(maxsize=1)
def get_spotify_client():
    """
    Returns a cached Spotify client. Will only authenticate once and reuse the client.
    """
    try:
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

        scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-modify-public playlist-modify-private user-library-read user-library-modify"

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            open_browser=False
        )

        # Check if we already have a valid token
        if not auth_manager.validate_token(auth_manager.cache_handler.get_cached_token()):
            # Get the authorization URL
            auth_url = auth_manager.get_authorize_url()
            logging.info(f"Waiting for user to visit the authorization URL: {auth_url}")

            # Wait for the authorization code from user
            # TODO: wait for telegram message with the code
            auth_code = input("Enter the authorization code: ")

            # Get access token using the authorization code
            auth_manager.get_access_token(auth_code)

        sp = spotipy.Spotify(auth_manager=auth_manager)
        return sp
    except Exception as e:
        logging.error(f"Error authenticating with Spotify: {str(e)}")
        raise

def play(context_variables, query: str, content_type: str = 'track'):
    """
    Search for and play Spotify content by name.

    Args:
        context_variables (dict): A dictionary containing context information.
        query (str): The name/query to search for.
        content_type (str): Type of content to play ('track', 'album', 'artist', 'playlist')
    """
    logging.info(f"Function called: play(context_variables={context_variables}, query='{query}', content_type='{content_type}')")

    sp = get_spotify_client()
    try:
        # Validate content type
        valid_types = {'track', 'album', 'artist', 'playlist'}
        if content_type not in valid_types:
            return f"<result><error>Invalid content type: '{content_type}'. Valid types are: {', '.join(valid_types)}</error></result>"

        # Search for the content
        results = sp.search(q=query, type=content_type, limit=1)

        items_key = f"{content_type}s"
        if not results[items_key]['items']:
            return f"<result><error>No {content_type} found matching: '{query}'</error></result>"

        item = results[items_key]['items'][0]

        # Play the content based on its type
        if content_type == 'track':
            sp.start_playback(uris=[item['uri']])
            result = f"""<result>
<message>Now playing track: {item['name']} by {item['artists'][0]['name']}</message>
<track_info>
    <name>{item['name']}</name>
    <artist>{item['artists'][0]['name']}</artist>
    <album>{item['album']['name']}</album>
    <duration>{item['duration_ms']}</duration>
</track_info>
</result>"""
        elif content_type == 'album':
            sp.start_playback(context_uri=item['uri'])
            result = f"""<result>
<message>Now playing album: {item['name']} by {item['artists'][0]['name']}</message>
<album_info>
    <name>{item['name']}</name>
    <artist>{item['artists'][0]['name']}</artist>
    <total_tracks>{item['total_tracks']}</total_tracks>
</album_info>
</result>"""
        elif content_type == 'artist':
            sp.start_playback(context_uri=item['uri'])
            result = f"""<result>
<message>Now playing top tracks from artist: {item['name']}</message>
<artist_info>
    <name>{item['name']}</name>
    <popularity>{item['popularity']}</popularity>
</artist_info>
</result>"""
        elif content_type == 'playlist':
            sp.start_playback(context_uri=item['uri'])
            result = f"""<result>
<message>Now playing playlist: {item['name']}</message>
<playlist_info>
    <name>{item['name']}</name>
    <owner>{item['owner']['display_name']}</owner>
    <tracks_total>{item['tracks']['total']}</tracks_total>
</playlist_info>
</result>"""

        logging.info(f"Function play() started playing {content_type}: {item['name']}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error playing {content_type}: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message

def get_current_track(context_variables):
    """
    Get information about the currently playing track.

    Args:
        context_variables (dict): A dictionary containing context information.
    """
    logging.info(f"Function called: get_current_track(context_variables={context_variables})")

    sp = get_spotify_client()  # Use cached client instead
    try:
        current = sp.current_playback()

        if not current or not current['item']:
            return "<result><message>No track currently playing</message></result>"

        track = current['item']
        result = f"""<result>
<track_info>
    <name>{track['name']}</name>
    <artist>{track['artists'][0]['name']}</artist>
    <album>{track['album']['name']}</album>
    <progress>{current['progress_ms']}</progress>
    <duration>{track['duration_ms']}</duration>
    <is_playing>{current['is_playing']}</is_playing>
</track_info>
</result>"""
        logging.info(f"Function get_current_track() returned current track info")
        return result
    except Exception as e:
        error_message = f"<result><error>Error getting current track: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message

def control_playback(context_variables, action: str):
    """
    Control playback (play, pause, next, previous).

    Args:
        context_variables (dict): A dictionary containing context information.
        action (str): The playback control action ('play', 'pause', 'next', 'previous')
    """
    logging.info(f"Function called: control_playback(context_variables={context_variables}, action='{action}')")

    sp = get_spotify_client()  # Use cached client instead
    try:
        if action == 'play':
            sp.start_playback()
            message = "Playback started"
        elif action == 'pause':
            sp.pause_playback()
            message = "Playback paused"
        elif action == 'next':
            sp.next_track()
            message = "Skipped to next track"
        elif action == 'previous':
            sp.previous_track()
            message = "Returned to previous track"
        else:
            return f"<result><error>Invalid action: {action}</error></result>"

        result = f"<result><message>{message}</message></result>"
        logging.info(f"Function control_playback() executed action: {action}")
        return result
    except Exception as e:
        error_message = f"<result><error>Error controlling playback: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message

def search(context_variables, query: str, search_type: str = 'track', limit: int = 5):
    """
    Search for items on Spotify.

    Args:
        context_variables (dict): A dictionary containing context information.
        query (str): The search query.
        search_type (str): Type of search ('album', 'artist', 'playlist', 'track', 'show', 'episode', 'audiobook').
        limit (int): Maximum number of results to return.
    """
    logging.info(f"Function called: search_items(context_variables={context_variables}, query='{query}', type='{search_type}', limit={limit})")

    sp = get_spotify_client()
    try:
        # Validate search type
        valid_types = {'album', 'artist', 'playlist', 'track', 'show', 'episode', 'audiobook'}
        if search_type not in valid_types:
            return f"<result><error>Invalid search type: '{search_type}'. Valid types are: {', '.join(valid_types)}</error></result>"

        results = sp.search(q=query, type=search_type, limit=limit)

        # Get the correct key from results based on search_type (Spotify adds 's' to the type)
        items_key = f"{search_type}s"
        if not results[items_key]['items']:
            return f"<result><message>No {search_type}s found matching: '{query}'</message></result>"

        items_info = []
        for item in results[items_key]['items']:
            if search_type == 'track':
                item_info = f"""<track>
    <name>{item['name']}</name>
    <artist>{item['artists'][0]['name']}</artist>
    <album>{item['album']['name']}</album>
    <duration>{item['duration_ms']}</duration>
    <uri>{item['uri']}</uri>
</track>"""
            elif search_type == 'album':
                item_info = f"""<album>
    <name>{item['name']}</name>
    <artist>{item['artists'][0]['name']}</artist>
    <total_tracks>{item['total_tracks']}</total_tracks>
    <uri>{item['uri']}</uri>
</album>"""
            elif search_type == 'artist':
                item_info = f"""<artist>
    <name>{item['name']}</name>
    <popularity>{item['popularity']}</popularity>
    <uri>{item['uri']}</uri>
</artist>"""
            elif search_type == 'playlist':
                item_info = f"""<playlist>
    <name>{item['name']}</name>
    <owner>{item['owner']['display_name']}</owner>
    <tracks_total>{item['tracks']['total']}</tracks_total>
    <uri>{item['uri']}</uri>
</playlist>"""
            elif search_type in {'show', 'episode', 'audiobook'}:
                item_info = f"""<{search_type}>
    <name>{item['name']}</name>
    <publisher>{item['publisher']}</publisher>
    <uri>{item['uri']}</uri>
</{search_type}>"""

            items_info.append(item_info)

        result = f"<result>\n{''.join(items_info)}\n</result>"
        logging.info(f"Function search_items() returned: {len(items_info)} {search_type}s")
        return result
    except Exception as e:
        error_message = f"<result><error>Error searching {search_type}s: {str(e)}</error></result>"
        logging.error(error_message)
        return error_message

if __name__ == "__main__":
    logging.info("Testing Spotify authentication...")
    try:
        sp = get_spotify_client()  # Use cached client instead
        logging.info("Spotify authentication successful!")
    except Exception as e:
        logging.error(f"Spotify authentication failed: {str(e)}")