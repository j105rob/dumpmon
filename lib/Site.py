from Queue import Queue
import requests
import time
import re
from pymongo import MongoClient
from requests import ConnectionError
from twitter import TwitterError
from settings import USE_DB, DB_HOST, DB_PORT, SEEN_DEQUE_LEN
import logging
import helper

from collections import deque

class Site(object):
    '''
    Site - parent class used for a generic
    'Queue' structure with a few helper methods
    and features. Implements the following methods:

            empty() - Is the Queue empty
            get(): Get the next item in the queue
            put(item): Puts an item in the queue
            tail(): Shows the last item in the queue
            peek(): Shows the next item in the queue
            length(): Returns the length of the queue
            clear(): Clears the queue
            list(): Lists the contents of the Queue
            download(url): Returns the content from the URL

    '''
    # I would have used the built-in queue, but there is no support for a peek() method
    # that I could find... So, I decided to implement my own queue with a few
    # changes
    def __init__(self, queue=None):
        
        # the double ended queue is used to check the last n URLs to see if they have been processed, since the URLs are random strings.
        self.seen = deque(maxlen=SEEN_DEQUE_LEN)
        
        if queue is None:
            self.queue = []
            
        if USE_DB:
            # Lazily create the db and collection if not present
            self.db_client = MongoClient(DB_HOST, DB_PORT).paste_db.pastes

    def addSeen(self,item):
        self.seen.append(item)
        #logging.info('[@] Site deque len %i'%(len(self.seen)))
        
    def hasSeen(self,item):
        res = item in self.seen
        #logging.info('[@] URL Seen %s %s'%(item.url,res))
        return res
        
    def empty(self):
        return len(self.queue) == 0

    def get(self):
        if not self.empty():
            result = self.queue[0]
            self.addSeen(result)
            del self.queue[0]
        else:
            result = None
        return result

    def put(self, item):
        self.queue.append(item)

    def peek(self):
        return self.queue[0] if not self.empty() else None

    def tail(self):
        return self.queue[-1] if not self.empty() else None

    def length(self):
        return len(self.queue)

    def clear(self):
        self.queue = []

    def list(self):
        print('\n'.join(url for url in self.queue))

    def parse(self):
        #override this
        pass
    
    def update(self):
        #override this
        pass
    
    def get_paste_text(self):
        #override this
        pass
    
    def monitor(self, bot):
        self.update()
        while(1):
            while not self.empty():
                #need to sleep to avoid the ban....
                #time.sleep(self.sleep/4)
                paste = self.get()
                logging.info('[*] Checking ' + paste.url)
                paste.text = self.get_paste_text(paste)
                tweet = helper.build_tweet(paste)
                if tweet:
                    logging.info(tweet)
                    with bot.tweetLock:
                        if USE_DB:
                            self.db_client.save({
                                'pid' : paste.id,
                                'text' : paste.text,
                                'emails' : paste.emails,
                                'hashes' : paste.hashes,
                                'num_emails' : paste.num_emails,
                                'num_hashes' : paste.num_hashes,
                                'type' : paste.type,
                                'db_keywords' : paste.db_keywords,
                                'url' : paste.url
                               })
                        try:
                            logging.debug('[+] Tweet %s'%(tweet))
                            bot.statuses.update(status=tweet)
                        except TwitterError as e:
                            logging.debug('[!] TwitterError %s'%(str(e)))
            self.update()
            while self.empty():
                logging.debug('[*] No results... sleeping')
                time.sleep(self.sleep)
                self.update()
