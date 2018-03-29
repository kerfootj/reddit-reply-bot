# replybot.py
# /u/PCAviator18
# 27/03/2018
# Python 3.6

import praw
import time
import sys
import traceback
import progressbar
from fuzzywuzzy import fuzz

__version__ = '1.0.0'

class bot:
	def __init__(self, keywords, quotes, subreddits=['all'], ratio=80, limit=250, sleeptime=30, debug=False):
		print('Setting up bot...')
		self.keywords = keywords
		self.quotes = quotes
		self.subreddits = subreddits
		self.ratio = ratio
		self.limit = limit
		self.sleeptime = sleeptime
		self.debug = debug
		self.numComments = 0
		self.timeout = 1
		self.reddit = None
	
	# Start the bot 
	def start(self):
		try:
			print('Logging in...')
			self._login()
			print('Logged in as ' + str(self.reddit.user.me()) + '\n')
			self.timeout = 10
			return self._run()
		except Exception as e:
			self._handle_exception(e)
	
	# Log in to the reddit account in praw.ini
	def _login(self):
		self.reddit = praw.Reddit('replybot', user_agent = 'replybot v{} by /u/PCAviator18'.format(__version__))
		
	def _run(self):
		while True:
			self._search_comments()
			print('Done searching comments')
			if self.numComments != 0:
				print('%d replies made' % self.numComments)
				self.numComments = 0
			self._sleep(self.sleeptime, 'Sleeping')
	
	# Search the comments for a fuzzy match to a provided phrase
	def _search_comments(self):
		
		# loop though all the subreddits in the list
		for sub in self.subreddits:
			subreddit = self.reddit.subreddit(sub)
			# loop through the posts in each subreddit
			for submission in subreddit.hot(limit = self.limit):
				
				usedQuotes = []
				
				print('Gettings comments for: ' + submission.title)
				start = time.time()
				submission.comments.replace_more(limit = 0)
				t = time.time() - start
				print("%.2f" %t + ' seconds to get ' + str(submission.num_comments) + ' comments\n')
				
				# Check each comment for a fuzzy match to one of the quotes
				for comment in submission.comments.list():
					for i in range(0, len(self.quotes)):
						if comment != None and comment.author != None:
							if comment.author.name != self.reddit.user.me():
								if self.keywords[i].upper() in comment.body.upper():
									if fuzz.ratio(self.quotes[i], comment.body) >= self.ratio:
										usedQuotes.append([self.quotes[i], comment])
							else:
								print('Already replied to this thread')
								break
						else:
							break
				
				# If a match was found try and reply to the comment
				if 0 < len(usedQuotes) and len(usedQuotes) < len(self.quotes):
					self._reply_to_comment(usedQuotes)
	
	# Provide a unused reply to a comment thread
	def _reply_to_comment(self, usedQuotes):
		d = dict(usedQuotes)
		for quote in self.quotes:
			if quote not in d:
				# Reply to the last relevant comment in the thread 
				comment = usedQuotes[len(usedQuotes)-1][1]
				print('Replying to a comment...\n')
				comment.upvote()
				reply = comment.reply(quote)
				self._log_comment(comment, reply)
				self.numComments += 1
				
				return
		print('All replies already taken...')
		return
	
	# Log the parent comment and reply 	
	def _log_comment(self, comment, reply):
		f = open('log.txt', 'a+')
		f.write(str(comment) + '\t\t' + str(reply) + '\r\n')
		f.close
		
	def _sleep(self, st, message):
		
		cur = 0
		t = 60 * st
		
		self._start_progress(message)
		while(cur < t):
			time.sleep(t / 10)
			cur = cur + (t / 10)
			self._progress(cur / t * 100)
		self._end_progress()
			
	
	def _start_progress(self, title):
		global progress_x
		sys.stdout.write(title + ': [' + '-'*40 + ']' + chr(8)*41)
		sys.stdout.flush()
		progress_x = 0
			
	def _progress(self, x):
		global progress_x
		x = int(x * 40 // 100)
		sys.stdout.write('#' * (x - progress_x))
		sys.stdout.flush()
		progress_x = x
		
	def _end_progress(self):
		sys.stdout.write('#' * (40 - progress_x) + ']\n\n')
		sys.stdout.flush()
		
	def _handle_exception(self, e):
		traceback.print_exc(limit=50)
		self._sleep(self.timeout, 'Timed out, wait to retry')
		self.timeout *= 2
		self.start()
		sys.exit(0)
		 
