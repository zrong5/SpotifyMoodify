from Methods import Moodify
import spotipy.util as util
import os
import sys

def main():
    # authorization credentials
    user_name = sys.argv[1]
    redirect_uri = "https://www.google.com/"
    scope = "user-library-read user-top-read playlist-modify-public user-follow-read"

    # authorize user 
    try:
        token = util.prompt_for_user_token(user_name, scope, client_id, client_secret, redirect_uri)
    except:
        os.remove(".cache-"+user_name)
        token = util.prompt_for_user_token(user_name, scope, client_id, client_secret, redirect_uri)

    Moodify(token)
    
if __name__ == "__main__": main()
