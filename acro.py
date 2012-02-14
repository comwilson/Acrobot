#!/usr/bin/python
#
# YAAB: Yet Another AcroBot - plays a game of acro on IRC
# Copyright (C) 2005 by Calvin Harding (Cenobite) <cenobite@enslaved.za.net>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

try:
	from psyco.classes import *
except ImportError:
	pass

import sys, string, random, ircbot, irclib, time, threading
true = 1
false = 0
version = "0.6.1b"

# CONFIGURATION STUFF GOES HERE
acro_time = 90 # Seconds to come up with an acro
vote_time = 45 # Seconds to vote on acros
start_acro= 3  # The number of letters in the first round
rounds    = 5  # Number of rounds (letters in acro goes up once each round
total_weight = 70 # Total weight. If you change one of the weight values, add or subtract this accordingly
weight   = [3, 3, 3, 3, 3, 4, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 2, 1, 2, 2]
          # A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T  U  V  W  X  Y  Z
alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
	   # Weight determines the chance that a certain letter will come up in an acro
	   # The higher the number, the greater chance. Tweak this if difficult letters come up
	   #  too often, etc.
	   # The alphabet prolly doesn't need to be modified, I just put it there because I need such
	   #  an array, and it looked like a good place to put it.
allow_doubles	= true 	# Allow the same letter twice in a row
allow_triples	= false # Allow the same letter three times in a row
servers		= [["lancre.lagnet.org.za", 6667, "b4nb0t"], ["dragon.lagnet.org.za", 6667]]
nick		= "Jester"
chan		= "#games"
chanowner	= "nooner"
botmaster	= "Cenobite"

# Colours and formatting. TODO: finish this and implement it!
bold		= "\x02"
normal		= "\x0F"
underline	= "\x1F"

red		= "\x0304"

# The builtin help system. This is a horrible kludge, but it works. :P
help_intro	= "YAAB - Yet Another AcroBot. Designed to mimic the behaviour of Rizen's Acrobot, but with (hopefully) better timing implementations, more options, colours, bigger muscles etc. Please send suggestions/complaints to cenobite@enslaved.za.net."
help_main01	= bold + red + "How to play acro: " + normal + "At the start of each round I will give you an acro (for example: lmao). You then have to make up a phrase to fit that acro (for example: leather makes ankles oily)."
help_main02	= "You enter your acro by typing /msg " + nick + " <your answer>"
help_main03	= "After the alotted time has passed, I will display a numbered list of all the acros entered and a vote will then be held to determine the winner. You must then pick your favourite acro and vote for it."
help_main04	= "You submit your vote by typing /msg " + nick + " <your vote> (" + bold + "note:" + normal + " you only have to type the number of your vote, for example /msg " + nick + " 5)"
help_main05	= "For more information, please ask " + chanowner + ", " + botmaster + " or one of the ops for help."
# END CONFIGURATION

class AcroBot(ircbot.SingleServerIRCBot):
	def __init__(self, serverlist, nick, chan):
		print "AcroBot online!"
		self.me = nick
		self.chan = chan
		
		self.rnd = random.Random(time.time())
		self.mode_switcher = threading.Timer(acro_time, self.switch_mode)
		self.vote_time = threading.Timer(vote_time, self.round)
				
		self.on = false
		self.scores = {}
		self.this_round_nicks = []
		self.this_round_acros = []
		self.voted = []
		self.this_round_scores = []
		self.which_round = 0
		self.acro = ""
		self.mode = ""
		
		ircbot.SingleServerIRCBot.__init__(self, serverlist, nick, "AcroBot")
		print "Connecting..."
		
		self.start()
		
	def disconnect(self):
		ircbot.SingleServerIRCBot.disconnect(self, "YAAB: Yet Another AcroBot-" + version + " by Cenobite")
		print "Disconnecting..."
		sys.exit()
		
	def round(self):
		for n in range(len(self.this_round_nicks)):
			if self.scores.has_key(self.this_round_nicks[n]):
				self.scores[self.this_round_nicks[n]] += self.this_round_scores[n]
			else:
				self.scores[self.this_round_nicks[n]] = self.this_round_scores[n]
					
		self.connection.privmsg(self.chan, "\x02\x0304Voting time is up!")
		for n in range(len(self.this_round_nicks)):
			if self.this_round_scores[n] > 0:
				self.connection.privmsg(self.chan, "\x1F\x0313" + self.this_round_nicks[n] + "'s\x0F \x02\x0312reponse was \x0F\x0306'" + self.this_round_acros[n] + "'\x0F\x02\x0312 and got \x0F\x02\x1F\x0313" + str(self.this_round_scores[n]) + "\x0F\x02\x0312 votes!")
		
		if self.which_round == rounds:
			self.endgame()
			return

		self.connection.privmsg(self.chan, "\x02\x0312The score stands at:")
		for nick in self.scores.keys():
			if self.scores[nick] > 0:
				self.connection.privmsg(self.chan, "\x02\x0313" + nick + "\x0312 with a score of \x0313" + str(self.scores[nick]) + "\x0312!")

		self.this_round_nicks = []
		self.this_round_acros = []
		self.voted = []
		self.this_round_scores = []
		
		self.which_round += 1
		self.gen_acro(start_acro + self.which_round - 1)
		self.mode = "ACRO"
		self.connection.privmsg(self.chan, "\x0304\x1FRound " + str(self.which_round) + "!\x0F \x0304The new acro is: \x02\x0303" + self.acro)
		threading.Timer(acro_time, self.switch_mode).start()
		
	def switch_mode(self):
		self.mode = "VOTE"
		self.connection.privmsg(self.chan, "\x02\x0304Acro time is up! Please vote now on the following choices:")
		for a in range(len(self.this_round_acros)):
			self.connection.privmsg(self.chan, "\x0306\x1F#" + str(a) + "\x0F: \x02\x0312" + self.this_round_acros[a])
		threading.Timer(vote_time, self.round).start()
		
	def startgame(self):
		# The following (hopefully) fixes a bug that carries
		# acros and scores across games
		self.scores = {}
		self.this_round_nicks = []
		self.this_round_acros = []
		self.voted = []
		self.this_round_scores = []

		self.which_round = 1
		self.on = true
		self.gen_acro(start_acro)
		self.mode = "ACRO"
		self.connection.privmsg(self.chan, "\x02\x0304Starting a new game of acro! Get ready!")
		self.connection.privmsg(self.chan, "\x0304\x1FRound " + str(self.which_round) + "!\x0F \x0304The new acro is: \x02\x0303" + self.acro)
		threading.Timer(acro_time, self.switch_mode).start()
	
	def endgame(self):
		msg = self.connection.privmsg
		msg(self.chan, "\x02\x0304The game is over!")
		msg(self.chan, "\x02\x0304Ending scores:")
		for nick in self.scores.keys():
			msg(self.chan, "\x0313\x1F" + nick + "\x0F\x02\x0312 with a score of \x0F\x1F\x0313" + str(self.scores[nick]) + "\x0F\x02\x0312!")
			
	def on_welcome(self, c, e):
		c.join(self.chan)
		c.privmsg(self.chan, "Hello! Try '/msg " + nick + " !help' for more info. Have fun! :) ")
		
	def on_privmsg(self, c, e):
		if string.split(e.arguments()[0])[0] == "!help":
			c.privmsg(irclib.nm_to_n(e.source()), help_intro)
			c.privmsg(irclib.nm_to_n(e.source()), help_main01)
			c.privmsg(irclib.nm_to_n(e.source()), help_main02)
			c.privmsg(irclib.nm_to_n(e.source()), help_main03)
			c.privmsg(irclib.nm_to_n(e.source()), help_main04)
			c.privmsg(irclib.nm_to_n(e.source()), help_main05)
		elif string.split(e.arguments()[0])[0] == "!start":
			self.startgame()
		elif string.split(e.arguments()[0])[0] == "!rehash":
			c.privmsg(self.chan, "Restarting...")
			self.start()
		elif string.split(e.arguments()[0])[0] == "!shutdown":
			c.privmsg(self.chan, "Have fun, bye!")
			self.disconnect()
		elif self.on == false:
			c.privmsg(e.source(), "Sorry, no game is currently running. Try '!help'.")
		elif self.mode == "ACRO":
			if self.confirm_acro(string.split(e.arguments()[0])) == false:
				c.notice(irclib.nm_to_n(e.source()), "That does not match the acro. Try again.")
				return
			else:
				if irclib.nm_to_n(e.source()) in self.this_round_nicks:
					c.notice(irclib.nm_to_n(e.source()), "You may not enter more than once.")
					return
				elif e.arguments()[0] not in self.this_round_acros:
					c.notice(irclib.nm_to_n(e.source()), "You've been entered in this round.")
					self.this_round_nicks.append(irclib.nm_to_n(e.source()))
					self.this_round_acros.append(e.arguments()[0])
					self.this_round_scores.append(0)
					return
				else:
					c.notice(irclib.nm_to_n(e.source()), "That acro has already been entered. Please try again.")
					return
		elif self.mode == "VOTE":
			try:
				vote = int(string.split(e.arguments()[0])[0])
				if irclib.nm_to_n(e.source()) not in self.this_round_nicks:
					c.notice(irclib.nm_to_n(e.source()), "You can't vote if you don't participate.")
					return
				if irclib.nm_to_n(e.source()) == self.this_round_nicks[vote]:
					c.notice(irclib.nm_to_n(e.source()), "You can't vote for yourself. Try again.")
					return
				if irclib.nm_to_n(e.source()) not in self.voted:
					self.this_round_scores[vote] += 1
					self.voted.append(irclib.nm_to_n(e.source()))
					c.notice(irclib.nm_to_n(e.source()), "Your vote has been counted.")
					return
			except ValueError:
				pass
					
				
	def confirm_acro(self, input):
		if len(input) != len(self.acro):
			return false
		for i in range(len(self.acro)):
			if string.capitalize(input[i])[0] != self.acro[i]:
				return false
		return true
	
	def gen_acro(self, length):
		self.acro = self.random_letter()
		letter = self.random_letter()
		if allow_doubles == false and self.acro[0] == letter:
			while self.acro[0] == letter:
				letter = self.random_letter()
		self.acro += letter
		
		for i in range(2, length):
			letter = self.random_letter()
			if allow_doubles == false and self.acro[i-1] == letter:
				while self.acro[i-1] == letter:
					letter = self.random_letter()
			if allow_triples == false and self.acro[i-1] == letter and self.acro[i-2] == letter:
				while self.acro[i-1] == letter:
					letter = self.random_letter()
			self.acro += letter
				
	def random_letter(self):
		n = self.rnd.randrange(0, total_weight-1)
		for l in range(len(alphabet)):
			if n < weight[l]:
				return alphabet[l]
			else:
				n -= weight[l]
		return alphabet[-1]

AcroBot(servers, nick, chan)

# TODO
#
#     Add '!stop' command
#     Only chanops should be allowed to use '!shutdown'
#     Make help system a bit more elegant
#     Clean up the colours and formatting
#

# Long term goals
#
#     Fully functional AI chatbot with games (including acro) ;)
#     SSL connection support
#     Rewrite the whole damn thing in C and asm
#

# Changelog:
#
# 0.6.1b
#
#     * Bot now autoidentifies to NickServ
#
# 0.6b
#
#     * Implemented built-in help system
#     * Quite alot of fixed bugs, so it's finally time to switch to a higher
#       minor version number. It is still beta though, and most of the
#       bugfixes haven't even been tested yet.
#
# 0.5.9b-r2
#
#     * Bot now recognizes when someone tries to enter more than one acro,
#       gives them a warning and ignores the subsequent acro.
#
# 0.5.9b-r1
#
#     * Hopefully fixed a bug that (undesirably) caused scores to be carried
#       over to the next game unless the bot was completely shutdown and
#       restarted.
#
# 0.5.9b:
#
#     * Fixed Colours to make them friendlier to light backgrounds
#     * Added '!rehash' command to restart the bot
#     * Bot now uses /notice instead of /msg for arbitrary messages. This fixes
#       a potential flood exploit and is more convenient.
#     * Help functionality added
#
# No prior Changelog available
