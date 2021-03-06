from .regexes import regexes
import settings
import logging
import re
import time

class Paste(object):
    def __init__(self,id):
        '''
        class Paste: Generic "Paste" object to contain attributes of a standard paste
        '''
        self.id = id
        self.emails = []
        self.emails2 = []
        self.hashes = []
        self.num_emails = 0
        self.num_hashes = 0
        self.text = None
        self.type = None
        self.sites = None
        self.db_keywords = 0.0
    
    def __eq__(self,comparePaste):
        #logging.info('id %s compares to %s'%(self.id, comparePaste.id))
        return self.id == comparePaste.id
    
    def row(self):
        return {
                'pid' : self.id,
                'text' : self.text,
                'emails' : self.emails,
                'hashes' : self.hashes,
                'num_emails' : self.num_emails,
                'num_hashes' : self.num_hashes,
                'type' : self.type,
                'db_keywords' : self.db_keywords,
                'url' : self.url,
                "added":time.strftime("%c")
               }
    
    def get(self):
        #override this
        logging.error('[@] Function Not Implemented in Subclass')
        pass
        
    def match(self):
        '''
        Matches the paste against a series of regular expressions to determine if the paste is 'interesting'

        Sets the following attributes:
                self.emails
                self.hashes
                self.num_emails
                self.num_hashes
                self.db_keywords
                self.type

        '''
        # Get the amount of emails
        try:
            r = self.text.splitlines()
            logging.debug("[*] Num Lines in text: %i"%(len(r)))           

            if regexes['email'].search(self.text):
                self.emails = regexes['email'].findall(self.text)
                
            if regexes['email2'].search(self.text):
                self.emails2 = regexes['email2'].findall(self.text)
            
            self.hashes = regexes['hash32'].findall(self.text)
            
            self.num_emails = len(self.emails)
            logging.debug("[*] Num Emails: %i"%(self.num_emails))
            
            self.num_emails = len(self.emails2)
            logging.debug("[*] Num Emails2: %i"%(self.num_emails))
            
            self.num_hashes = len(self.hashes)
            logging.debug("[*] Num Hashes: %i"%(self.num_hashes))
            
            if self.num_emails > 0:
                self.sites = list(set([re.search('@(.*)$', email).group(1).lower() for email in self.emails]))
                logging.debug("[*] Num Sites: %i"%(len(self.sites)))
                
            for regex in regexes['db_keywords']:
                if regex.search(self.text):
                    logging.debug('\t[+] ' + regex.search(self.text).group(1))
                    self.db_keywords += round(1/float(
                        len(regexes['db_keywords'])), 2)
                    
            for regex in regexes['blacklist']:
                if regex.search(self.text):
                    logging.debug('\t[-] ' + regex.search(self.text).group(1))
                    self.db_keywords -= round(1.25 * (
                        1/float(len(regexes['db_keywords']))), 2)
                    
            if (self.num_emails >= settings.EMAIL_THRESHOLD) or (self.num_hashes >= settings.HASH_THRESHOLD) or (self.db_keywords >= settings.DB_KEYWORDS_THRESHOLD):
                self.type = 'db_dump'
                
            if regexes['cisco_hash'].search(self.text) or regexes['cisco_pass'].search(self.text):
                self.type = 'cisco'
                
            if regexes['honeypot'].search(self.text):
                self.type = 'honeypot'
                
            if regexes['google_api'].search(self.text):
                self.type = 'google_api'
                
            # if regexes['juniper'].search(self.text): self.type = 'Juniper'
            for regex in regexes['banlist']:
                if regex.search(self.text):
                    self.type = None
                    break
    
            logging.debug("[*] Type: %s"%(self.type))    
            return self.type
        
        except Exception as e:
            logging.error("[!] Error: %s"%(str(e)))
            return None
