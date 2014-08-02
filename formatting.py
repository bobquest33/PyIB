import string
import cgi
import re

from settings import Settings
from database import *

def tripcode(pw):
  """
  Calculate tripcode to match output of most imageboards
  """
  from crypt import crypt
  
  try:
    pw = pw.encode("sjis", "ignore")
  except:
    pass
  
  pw = pw.replace('"', "&quot;") \
         .replace("'", "'")      \
         .replace("<", "&lt;")   \
         .replace(">", "&gt;")   \
         .replace(",", ",")
  salt = re.sub(r"[^\.-z]", ".", (pw + "H..")[1:3])
  salt = salt.translate(string.maketrans(r":;=?@[\]^_`", "ABDFGabcdef"))
    
  return crypt(pw, salt)[-10:]

def nameBlock(post_name, post_tripcode, post_email, post_timestamp_formatted):
  """
  Creates a string containing HTML formatted poster name data.  This saves quite
  a bit of time when templating pages, as it saves the engine a few conditions
  per post, which adds up over the time of processing entire pages
  """
  board = Settings._.BOARD
  nameblock = ""
  
  if post_name == "" and post_tripcode == "":
    post_anonymous = True
  else:
    post_anonymous = False
  
  if board["settings"]["anonymous"] == "" and (post_anonymous or board["settings"]["forced_anonymous"]):
    if post_email:
      nameblock += '<a href="mailto:' + post_email + '">'
    nameblock += post_timestamp_formatted
    if post_email:
      nameblock += "</a>"
  else:
    if post_anonymous:
      nameblock += '<span class="postername">'
      if post_email:
        nameblock += '<a href="mailto:' + post_email + '">' + board['settings']['anonymous'] + '</a>'
      else:
        nameblock += board["settings"]["anonymous"]
      nameblock += "</span>"
    else:
      if post_email:
        nameblock += '<a href="mailto:' + post_email + '">'
      nameblock += '<span class="postername">'
      if post_name:
        nameblock += post_name
      else:
        if not post_tripcode:
          nameblock += board["settings"]["anonymous"]
      if post_tripcode:
        nameblock += '</span><span class="postertrip">' + board['settings']['tripcode_character'] + post_tripcode
      nameblock += "</span>"
      if post_email:
        nameblock += "</a>"
    nameblock += " " + post_timestamp_formatted
    
  return nameblock

def cleanString(string, escape=True):
  string = string.strip()
  if escape:
    string = cgi.escape(string)
  return string

def clickableURLs(message):
  prog = re.compile(r"\b(http|ftp|https)://\S+(\b|/)|\b[-.\w]+@[-.\w]+")
  i = 0
  urllist = []
  while 1:
    m = prog.search(message, i)
    if not m:
      break
    j = m.start()
    urllist.append(message[i:j])
    i = j
    url = m.group(0)
    while url[-1] in '();:,.?\'"<>':
      url = url[:-1]
    i = i + len(url)
    if ':' in url:
      repl = '<a href="%s">%s</a>' % (url, url)
    else:
      repl = '<a href="mailto:%s">&lt;%s&gt;</a>' % (url, url)
    urllist.append(repl)
  j = len(message)
  urllist.append(message[i:j])
  return string.join(urllist, "")

def checkRefLinks(message, parentid):
  """
  Check for >># links in posts and replace with the HTML to make them clickable
  """
  board = Settings._.BOARD

  message = re.compile(r"&gt;&gt;([0-9]+)").sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(parentid) + r'.html#\1" onclick="javascript:highlight(' + '\'' + r'\1' + '\'' + r', true);">&gt;&gt;\1</a>', message)
  
  return message

def matchCrossThreadRefLinks(matchobj):
  board = Settings._.BOARD
  postid = matchobj.group(1)
  try:
    parentid = FetchOne("SELECT `parentid` FROM `posts` WHERE `id` = '%s' AND `boardid` = '%s' LIMIT 1" % (postid, board['id']))["parentid"]
  except:
    return matchobj.group(0)
  if parentid == "0":
    parentid = postid

  return '<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(parentid) + '.html#' + postid + '">&gt;&gt;&gt;&shy;' + postid + '</a>'

def checkCrossThreadRefLinks(message):
  """
  Check for >>># links in posts and replace with the HTML to make them clickable
  """
  board = Settings._.BOARD
  
  message = re.compile(r"&gt;&gt;&gt;([0-9]+)").sub(matchCrossThreadRefLinks, message)
  
  return message

def checkQuotes(message):
  """
  Check for >text in posts and add span around it to color according to the css
  """
  message = re.compile(r"^&gt;(.*)$", re.MULTILINE).sub(r'<span class="unkfunc">&gt;\1</span>', message)
  
  return message

def escapeHTML(string):
  string = string.replace('<', '&lt;')
  string = string.replace('>', '&gt;')
  return string

def matchPre(matchobj):
  return "<pre>" + matchobj.group(1).replace("\n", "") + "</pre>"

def matchAA(matchobj):
  return "<div class=\"aa\">" + matchobj.group(1).replace("\n", "") + "</div>"

def onlyAllowedHTML(message):
  """
  Allow <b>, <i>, <u>, <strike>, and <pre> in posts, along with the special <aa>
  """
  message = re.compile(r"&lt;b&gt;(.+?)&lt;/b&gt;", re.DOTALL | re.IGNORECASE).sub(r"<b>\1</b>", message)
  message = re.compile(r"&lt;i&gt;(.+?)&lt;/i&gt;", re.DOTALL | re.IGNORECASE).sub(r"<i>\1</i>", message)
  message = re.compile(r"&lt;u&gt;(.+?)&lt;/u&gt;", re.DOTALL | re.IGNORECASE).sub(r"<u>\1</u>", message)
  message = re.compile(r"&lt;strike&gt;(.+?)&lt;/strike&gt;", re.DOTALL | re.IGNORECASE).sub(r"<strike>\1</strike>", message)
  message = re.compile(r"&lt;pre&gt;(.+?)&lt;/pre&gt;", re.DOTALL | re.IGNORECASE).sub(matchPre, message)
  message = re.compile(r"&lt;aa&gt;(.+?)&lt;/aa&gt;", re.DOTALL | re.IGNORECASE).sub(matchAA, message)
  
  return message

def markdown(message):
  import markdown
  if message.strip() != "":
    return markdown.markdown(message).rstrip("\n").rstrip("<br>")
  else:
    return ""
