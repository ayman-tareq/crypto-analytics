import requests
from datetime import datetime
import regex

headers = {
    "x-rapidapi-key": "dd82b0660fmsh5863e3f388ab998p178600jsn5e8f3d4b7f77",
    "x-rapidapi-host": "twitter154.p.rapidapi.com"
}

TWEETS_LIMIT = 40

def remove_emojis(text):
    return regex.sub(r'\p{Emoji}', '', text)

def is_enough_search(token, tweets):
    if token == '' or len(tweets) >= TWEETS_LIMIT:
        print('Enough Tweets Collected!')
        return True
    else: 
        print('Not Enough Search:', len(tweets))
        return False
    
def send_requests_4_tweets(username, headers, token=''):
    if not token:
        url = "https://twitter154.p.rapidapi.com/user/tweets"
        querystring = {"username":username,"limit":"50","include_replies":"false","include_pinned":"false"}
    else:
        url = "https://twitter154.p.rapidapi.com/user/tweets/continuation"
        querystring = {"username":username,"limit":"50","continuation_token":token,"include_replies":"false"}
    
    print(querystring)
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()

def get_tweets(username):
    
    tweets = []
    token = ''
    
    while True:
        data = send_requests_4_tweets(username, headers, token)
        token = data.get('continuation_token', '')
        items = data.get('results', [])
        
        for item in items:
            # break
            # text = remove_emojis(item['text'])
            text = item['text']

            timestamp = item['timestamp']
            human_readable_date = datetime.fromtimestamp(timestamp).strftime('%d %B %Y, %H:%M:%S')
            
            tweets.append({
                'published_at': human_readable_date,
                'text': text
            })
        if is_enough_search(token, tweets):
            return tweets
        

if __name__ == '__main__':
    username = 'ayman_tareq97'
    tweets = get_tweets(username)