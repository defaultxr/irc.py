#!/usr/bin/env python
# PyIRC v1.0 -- http://k-pdt.net/pyirc/
import socket
from time import time, sleep
from random import choice
from re import match
def IRCConvert(string):
 """This is for converting the formatting (underline, color, etc..) in an IRC string to the formatting for a Linux shell.  I'm not sure if this will work for Windows."""
 if string == None: return
 u = 0
 b = 0
 r = 0
 c = -3 # -3 is none, -2 means next char is the first color number, and -1 means next char is the second color number.
 rc = -3 # -3 is no reverse color, -2 means next char is the first reverse color number, and -1 means next char is the second reverse color number.
 cf = '' # current format string.
 result = ''
 for i in string:
  if i == '\017':
   result += chr(0x1b) + "[0m" # clearing all
   cf = ''
   u = 0
   b = 0
   r = 0
   c = -3
   rc = -3
  elif i == '\002' and b == 1: # clearing bold
   result += chr(0x1b) + "[0m"
   cf = cf.replace(chr(0x1b) + "[1m", '')
   result += cf
   b = 0
  elif i == '\002' and b == 0: # adding bold
   result += chr(0x1b) + "[1m"
   cf += chr(0x1b) + "[1m"
   b = 1
  elif i == '\026' and r == 1: # clear reverse
   result += chr(0x1b) + "[0m"
   cf = cf.replace(chr(0x1b) + "[7m", '')
   result += cf
   r = 0
  elif i == '\026' and r == 0: # add reverse
   result += chr(0x1b) + "[7m"
   cf += chr(0x1b) + "[7m"
   r = 1
  elif i == '\037' and u == 1: # clear underline
   result += chr(0x1b) + "[0m"
   cf = cf.replace(chr(0x1b) + "[4m", '')
   result += cf
   u = 0
  elif i == '\037' and u == 0: # add underline
   result += chr(0x1b) + "[4m"
   cf += chr(0x1b) + "[4m"
   u = 1
  else:
   result += i
 return result + chr(0x1b) + "[0m"
class IRCError:
 """In case of an error in the script, report it to defaultxr@gmail.com with the FULL error message and the last message the bot received from IRC, if possible."""
 def __init__(self):
  pass
class newSocket(socket.socket):
 def send(self, text):
  return super(newSocket, self).send(bytes(text, 'utf-8'))
class IRC:
 def __init__(self, host, nick, snick='Bot' + str(choice(list(range(99999)))), port=6667, ident='PyIRC', realname='PyIRC Bot www.k-pdt.net/pyirc', prnt=False):
  """host = net address (i.e.: irc.chatspike.net)
  nick = bot's nick (i.e.: aBot)
  snick = bot's substitute nick (i.e.: aBot2).  Defaults to 'Bot' with a random number appended.
  port = server port.  defaults to 6667.
  ident = bot ident.  defaults to 'PyIRC'.
  realname = bot realname.  defaults to 'PyIRC Bot www.k-pdt.net/pyirc'.
  prnt = whether or not to print events that the bot performs (i.e.: when you call self.msg or self.join)  If you have global prnting enabled but want to disable printing for a specific command, append prnt=False to that command's arguments.  For example:
  
  self.msg("NickServ", "identify PASSWORD", prnt=False)
  
  That way, your password will not be printed.  You cannot enable prnting for a specific command if global prnting is disabled.
  
  If you want the bot to connect, fill in these args and then invoke the connect() method...
   f = IRC('irc.chatspike.net', 'aBot', ident='aBot', realname='aBot Beta')
   f.connect()
  
  If you want your bot to do something besides idle, you have to overwrite the respective on_* method of the class.  For example:
   class xIRC(IRC):
    def on_privmsg(self, nick, ident, host, target, msg):
     if 'foo' in msg and target[:1] == '#':
      print '%s said foo!' % nick
      self.kick(target, nick, "Don't say foo!")
  
  In the above case, the bot would kick a user when they said 'foo' in a channel."""
  self.host = host # this is the server address, i.e.: irc.chatspike.net.
  self.prinick = nick
  self.subnick = snick
  self.port = port
  self.ident = ident
  self.realname = realname
  self.prnt = prnt
  self.curnick = None
  self.nn = 0 # network number if server is a tuple or list so the bot can cycle servers.
  self.timeout = 121
  try:
   if type(self.host) == list or type(self.host) == tuple:
    self.netname = self.host[self.nn].split('.')[-2]
   else:
    self.netname = self.host.split('.')[-2]
  except IndexError:
   if type(self.host) == list or type(self.host) == tuple:
    self.netname = self.host[self.nn][:]
   else:
    self.netname = self.host[:]
 def connect(self):
  """connect() starts the whole process of connecting to IRC, sending nick, username, etc.  connect() runs the "while 1" loop that processes incoming text from IRC as well.  This method will run until you close the bot."""
  global time
  self.sock = newSocket() #socket.socket()
  try:
   if type(self.host) == list or type(self.host) == tuple:
    hst_tmp = self.host[self.nn]
   else:
    hst_tmp = self.host
   if self.prnt:
    print(" => Connecting to %s/%s..." % (hst_tmp, self.port))
   self.sock.connect((hst_tmp, self.port))
  except socket.gaierror:
   self.nn += 1
   if (type(self.host) == list or type(self.host) == tuple) and len(self.host) <= self.nn:
    self.nn = 0
   self.on_disconnected('ConnectFail')
   return
  except socket.error:
   self.nn += 1
   if (type(self.host) == list or type(self.host) == tuple) and len(self.host) <= self.nn:
    self.nn = 0
   self.on_disconnected('ConnectFail')
   return
  self.s_nick()
  self.s_user()
  readbuffer = ''
  self.sock.settimeout(float(self.timeout))
  while 1:
   try:
    f = self.sock.recv(1024)
   except KeyboardInterrupt:
    self.on_keyboardinterrupt()
    return "SelfQuit"
   except socket.timeout:
    if time() - self.lastget >= 242:
     self.on_disconnected('PingOut')
     return "PingOut"
   except socket.error:
    self.on_disconnected('ConnectionReset')
    return "ConnectionReset"
   try:
    readbuffer = readbuffer + f.decode()
   except UnicodeDecodeError:
    print("--- Unicode Decode Error 1 ---")
    try:
     readbuffer = readbuffer + str(f, 'utf-8')
    except UnicodeDecodeError:
     print("--- Unicode Decode Error 2 ---")
     readbuffer = readbuffer + str(f, 'utf-16', 'ignore')
   temp = readbuffer.split('\n')
   readbuffer = temp.pop()
   for line in temp:
    line = line.rstrip()
    input = line[:]
    line = line.split()
    self.lastget = time()
    if line[0] == 'PING':
     self.pong(line[1])
    elif match('^:(\S+)\s+PONG\s+(\S+)\s+:\d+$', input) != None:
     continue
    else:
     self.on_get_input(input) #after this, start sorting input by type and route it to the right def.
     if line[1] == '376': # end of motd.
      self.on_end_of_motd()
     if line[1] == 'MODE' and line[2].lower() == self.curnick.lower(): # MODE for user.
      try:
       self.on_user_mode(match('^:.*?:(.+)', input).groups()[0])
      except:
       self.on_user_mode(line[3])
     elif line[1] == 'NOTICE': # on NOTICE.
      tmpaddr = line[0][1:]
      if match('^(.*)!(.*)@(.*)$', tmpaddr) == None:
       #try:
       self.on_server_notice(tmpaddr, line[2], match('^:.*?:(.+)$', input).groups()[0])
       #except:
       # print("ERROR LINE: " + input)
      else:
       nick, ident, host = match('^(.*)!(.*)@(.*)$', tmpaddr).groups()
       target = line[2]
       msg = match('^:.*?:(.*)$', input).groups()[0]
       self.on_notice(nick, ident, host, target, msg)
     elif line[1] == 'PRIVMSG': #on PRIVMSG
      tmpaddr = line[0][1:]
      if match('^(.*)!(.*)@(.*)$', tmpaddr) == None:
       self.on_server_msg(match('^:.*?:(.+)$', input).groups()[0])
      else:
       nick, ident, host = match('^(.*)!(.*)@(.*)$', tmpaddr).groups()
       target = line[2]
       try:
        msg = match('^:.*?:(.+)$', input).groups()[0]
       except AttributeError:
        msg = ' '
       if msg[0] == '\001' and msg[-1] == '\001' and msg[1:7] != 'ACTION':
        self.on_ctcp(nick, ident, host, target, msg[1:-1])
       else:
        self.on_privmsg(nick, ident, host, target, msg)
     elif line[1] == 'JOIN': # on any JOIN
      tmpaddr = line[0][1:]
      nick, ident, host = match('^(.*)!(.*)@(.*)$', tmpaddr).groups()
      if nick == self.curnick: # if you're joining a channel.
       c = match('^:.*:?(#.+)$', input).groups()[0]
       self.on_you_join(c)
      else:
       nick, ident, host = match('^:(.*?)!(.*?)@(.*?)\s+.*$', input).groups()
       channel = match('^:(.+?):(#.+)', input).groups()[1]
       self.on_join(nick, ident, host, channel)
     elif line[1] == 'MODE' and line[2].lower() != self.curnick.lower(): # non-user MODE
      # A round of applause to Xeccos and Zeccoz.
      try:
       nick, ident, host = match('^:(.*?)!(.*?)@(.*?)\s+.+', input).groups()
      except AttributeError:
       nick = match('^:(\S+).+$', input).groups()
       ident = ''
       host = ''
      channel, mode = match('^:\S+\s+\S+\s+(\S+)\s+(.+)', input).groups()
      self.on_channel_mode(nick, ident, host, channel, mode)
     elif line[1] == 'PART':
      nick, ident, host, channel, msg = match('^:(.*?)!(.*?)@(\S+)\s+PART\s+:?(\S+)\s*:?(.+)?', input).groups()
      if nick.lower() == self.curnick.lower():
       self.on_you_part(channel, msg)
      else:
       if msg == None: msg = ''
       self.on_part(nick, ident, host, channel, msg)
     elif line[1] == 'QUIT': # on user quit.
      nick, ident, host, msg = match('^:(.*?)!(.*?)@(.*?)\s+\S+\s+:(.+)$', input).groups()
      self.on_quit(nick, ident, host, msg)
     elif line[1] == 'TOPIC': # on topic change.
      nick, ident, host, channel, topic = match('^:(.*?)!(.*?)@(.*?)\s+\S+\s+(\S+)\s+:(.+)$', input).groups()
      self.on_topic_change(nick, ident, host, channel, topic)
     elif line[1] == 'NICK': # on nick change.
      oldnick, ident, host, newnick = match('^:(.*?)!(.*?)@(.*?)\s+\S+\s+(\S+)$', input).groups()
      self.on_nick(oldnick, ident, host, newnick)
     elif line[1] == 'AUTH' and line[0] == 'NOTICE':
      self.on_server_notice(self.host, 'AUTH', match('^.+?:(.+)$', input).groups()[0])
     elif line[1] == 'KICK':
      #:K3V!~DefaultXR@ChatSpike-B728CFDA530BD8D8.ez-net.com KICK #k-pdt Kyndlr :test
      tmp = match('^:(.*?)!(.*?)@(.*?)\s+\S+\s+(\S+)\s+(\S+)\s*:?(.+)?$', input)
      if len(tmp.groups()) == 6:
       nick, ident, host, channel, kicked, msg = tmp.groups()
      else:
       nick, ident, host, channel, kicked = tmp.groups()
       msg = ''
      self.on_kick(nick, ident, host, channel, kicked, msg)
     elif line[0] == 'ERROR':
      self.on_disconnected('PingOut')
      return "PingOut"
     else:
      self.on_unknown_event(input)
 def s_nick(self, usn=0):
  """This subroutine sends the server your nick and sets self.curnick to the sent nick.  A different subroutine in this module will detect if the client's nick is changed, and will re-set self.curnick accordingly."""
  try:
   if usn == 0:
    self.sock.send("NICK %s\r\n" % self.prinick)
    self.curnick = self.prinick[:]
   else:
    self.sock.send("NICK %s\r\n" % self.subnick)
    self.curnick = self.subnick[:]
  except:
   self.on_disconnected('ConnectFail')
   return "ConnectFail"
 def s_user(self):
  """This subroutine sends the ident and realname to the server."""
  self.sock.send("USER %s %s bla :%s\r\n" % (self.ident, self.host, self.realname))
 def on_get_input(self, input):
  """This is called when any IRC message is received, and it's called before any other on_* method.
  
  'input' is the full unaltered text of the message received from the server."""
  pass
 def pong(self, num):
  self.sock.send("PONG %s\r\n" % num)
 def on_notice(self, nick, ident, host, target, msg):
  """This is called when the client receives a notice from someone.  What separates this from the on_server_notice method is that this is called when the hostmask of the message sender is in *!*@* form.  If the hostmask lacks a ! and a @, it is assumed to be a message directly from the server.
  
  'nick' is the nick of the message sender.
  'ident' is the ident of the message sender.
  'host' is the host of the message sender.
  'target' is who the notice is directed at--usually you (it will be the PyIRC client's nick, i.e.: aBot) or a channel.
  'msg' is the message sent."""
  pass
 def on_privmsg(self, nick, ident, host, target, msg):
  """This is called when the client receives a message (aka PRIVMSG) from someone.  Most commonly, PRIVMSGs are broadcasted to channels...
  
  'nick' is the nick of the sender.
  'ident' is the ident of the sender.
  'host' is the host of the sender.
  'target' is who the message was directed at--usually you (it will be the PyIRC client's nick) or a channel.
  'msg' is the message sent."""
  pass
 on_msg = on_privmsg # alias on_msg to on_privmsg.
 def on_join(self, nick, ident, host, channel):
  """This is called when someone else joins a channel that you are on. on_you_join is the method called when you join a channel."""
  pass
 def on_user_mode(self, mode):
  pass
 def on_channel_mode(self, nick, ident, host, channel, mode):
  pass
 def on_unknown_event(self, input):
  """This is called when PyIRC doesn't understand a message.  Feel free to overload this in your script.
  
  PyIRC's philosophy used to be to provide an event for every IRC code, but now we only cover the basics.  Consequently, this event will be called a lot.  If you need to use data from an event that is not covered by the event handlers built into PyIRC, then you will have to overload this and parse the input yourself.
  
  Currently PyIRC covers these events:
  MODE, NOTICE, JOIN, PRIVMSG, JOIN, PART, QUIT, TOPIC, NICK, AUTH, KICK
  
  Server PINGs are automatically responded to.
  CTCPs are routed to their own event (instead of being routed to on_privmsg).
  MODEs are separated into user modes (modes the server sets on users) and channel modes (modes set in channels on users by other users)
  Disconnections are also handled.
  
  'input' is the full line of text that PyIRC did not recognize."""
  pass
 def on_you_part(self, channel, msg):
  pass
 def on_part(self, nick, ident, host, channel, msg):
  pass
 def on_topic_change(self, nick, ident, host, channel, topic):
  pass
 on_topic = on_topic_change #link on_topic to on_topic_change
 def on_quit(self, nick, ident, host, msg):
  pass
 def on_nick(self, oldnick, ident, host, newnick):
  pass
 def on_disconnected(self, err):
  pass
 def on_keyboardinterrupt(self):
  self.quit()
 def on_ctcp(self, nick, ident, host, target, msg):
  pass
 def on_kick(self, nick, ident, host, channel, kicked, msg):
  pass
 def on_server_notice(self, address, target, msg):
  pass
 def on_server_msg(self, msg):
  pass
 def on_you_join(self, channel):
  pass
 def on_end_of_motd(self):
  pass
 def raw_send(self, data, prnt=True):
  """This sends the server the text of 'data' without any modifications.  Using line ends is not necessary; this function adds them automatically."""
  if self.prnt and prnt:
   print(' => Raw_Send: %s' % data.rstrip())
  self.sock.send(data.rstrip() + '\r\n')
 def msg(self, target, data, prnt=True):
  if self.prnt and prnt:
   print(' => Msg: (%s) %s' % (target, data))
  self.sock.send('PRIVMSG %s :%s\r\n' % (target, data))
 def me(self, target, data, prnt=True):
  if self.prnt and prnt:
   print(' => Acting: (%s) %s' % (target, data))
  self.sock.send('PRIVMSG %s :\001%s\001\r\n' % (target, data))
 def notice(self, target, data, prnt=True):
  if self.prnt and prnt:
   print(' => Noticing: (%s) %s' % (target, data))
  self.sock.send('NOTICE %s :%s\r\n' % (target, data))
 def quit(self, msg="", prnt=True):
  if self.prnt and prnt:
   print(' => Quitting: (%s) %s' % (self.netname, msg.rstrip()))
  try:
   self.raw_send('QUIT :%s' % msg, prnt=False)
   self.sock.shutdown(2)
   self.on_disconnected('SelfQuit')
   self.sock.close()
  except:
   pass
 def mode(self, target, mode, prnt=True):
  if self.prnt and prnt:
   print(' => Modes: (%s) %s' % (target, mode))
  self.sock.send('MODE %s %s\r\n' % (target, mode))
 def join(self, channel, prnt=True):
  if self.prnt and prnt:
   print(' => Joining: %s' % channel)
  self.sock.send('JOIN %s\r\n' % channel)
 def part(self, channel, msg=None, prnt=True):
  if self.prnt and prnt:
   print(' => Parting: (%s) %s' % (channel, msg))
  if msg == None:
   self.sock.send('PART %s\r\n' % channel)
  else:
   self.sock.send('PART %s :%s\r\n' % (channel, msg))
 def ctcp(self, target, text, prnt=True):
  if self.prnt and prnt:
   print(' => CTCP (%s) %s' % (target, text))
  self.sock.send('PRIVMSG %s :\001%s\001\r\n' % (target, text))
 def nctcp(self, target, text, prnt=True):
  """CTCP in notice form.  This is usually how you respond to CTCP requests."""
  if self.prnt and prnt:
   print(' => NCTCP (%s) %s' % (target, text))
  self.sock.send('NOTICE %s :\001%s\001\r\n' % (target, text))
 def topic(self, channel, topic, prnt=True):
  if self.prnt and prnt:
   print(' => Topics: (%s) %s' % (channel, topic))
  self.sock.send('TOPIC %s :%s\r\n' % (channel, topic))
 def kick(self, channel, who, msg='', prnt=True):
  if self.prnt and prnt:
   print(' => Kicking: (%s/%s) %s' % (who, channel, msg))
  if msg == '':
   self.sock.send('KICK %s %s\r\n' % (chanel, who))
  else:
   self.sock.send('KICK %s %s :%s\r\n' % (channel, who, msg))
 def nick(self, nick, prnt=True):
  if self.prnt and prnt:
   print(' => Nick: %s -> %s' % (self.curnick, nick))
  self.raw_send("NICK :%s" % nick)
  self.curnick = nick
