# Python code to illustrate parsing of XML files
# importing the required modules
import requests
import urllib.parse
from bs4 import BeautifulSoup
import sqlite3
import traceback
import os
sqlconnection = sqlite3.connect('/data/subs.db')
cursor1 = sqlconnection.cursor()
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext


def hello(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Hello {update.effective_user.first_name}')



# SQL command to create a table in the database

PREFIX="subs_"

def addobject(obj,data):
    types=""
    inserttypes=""
    insertqmarks=""
    values=tuple()
    for k,v in data.items():
        t = "TEXT"
        if(type(v)==int):
            t="INT"
        if(type(v)==float):
            t="FLOAT"
        
        types+=", "+k+" "+t
        inserttypes+=", "+k
        insertqmarks+=",?"
        values+=(v,)
        pass
    cursor1 = sqlconnection.cursor()
    sql_command="""CREATE TABLE IF NOT EXISTS """+PREFIX+obj+""" ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, 
    datecreated TEXT"""+types+""");"""
    # execute the statement
    cursor1.execute(sql_command)
    sql = "INSERT INTO "+PREFIX+obj+" (datecreated"+inserttypes+") VALUES (datetime('now')"+insertqmarks+");"
    #print(sql)
    #print(values)
    cursor1.execute(sql,values)
    sqlconnection.commit()
    return cursor1.lastrowid
def sqlfind(table,col,val):
    cursor = sqlconnection.cursor()
    try:
        cursor.execute("SELECT * FROM "+PREFIX+table+" WHERE "+col+" = ? ",(val,))
        return cursor.fetchone()
    except:
        return None
def sqlgetall(table,field="*"):
    try:
        cursor = sqlconnection.cursor()
        cursor.execute("SELECT "+field+" FROM "+PREFIX+table)
        return cursor
    except Exception as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
        return None
def loadRSS(channel):

    # url of rss feed
    url = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + \
        urllib.parse.quote_plus(channel)
    #print(url)
    # creating HTTP response object from given url
    try:
        resp = requests.get(url)
    except Exception as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
        time.sleep(3)
    return resp.content
TOKEN = os.environ['TELEGRAM_TOKEN']
bot_token = TOKEN
bot_chatID = os.environ['TELEGRAM_CHATID']
def telegram_bot_sendtext(bot_message):

    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' +urllib.parse.quote_plus( bot_message.replace("_","\\_"))

    response = requests.get(send_text)

    return response.json()   
def loadchannel(chan,sendtel=True):
    # calling main function
    soup = BeautifulSoup(loadRSS(chan), 'lxml')
    #print(soup)
    ytchanid=soup.find("feed").find("yt:channelid").text
    #print(ytchanid)
    chan=sqlfind("ytchannel","channelid",ytchanid)
    
    chanid=-1
    if(chan==None):
        ytchanid=soup.find("feed").find("yt:channelid").text
        #print(ytchanid)
        chanid=addobject("ytchannel",{
            "channelid":ytchanid,
            "name":soup.find("feed").find("author").find("name").text,
            "uri":soup.find("feed").find("author").find("uri").text,
            "published":soup.find("feed").find("published").text
        })
        print("got here")
    else:
        chanid=chan[0]
    for entry in soup.find("feed").find_all("entry"):
        #print(entry.find("yt:videoid").text)
        vidid=entry.find("yt:videoid").text
        vid=sqlfind("ytvideos","videoid",vidid)
        data={
                "channel":chanid,
                "videoid":vidid,
                "title":entry.find("title").text,
                "published":entry.find("published").text,
                "updated":entry.find("updated").text,
                "thumbnail":entry.find("media:group").find("media:thumbnail")["url"],
                "description":entry.find("media:group").find("media:description").text,
                "views":int(entry.find("media:community").find("media:statistics")["views"]),
                "rating":int(entry.find("media:community").find("media:starrating")["count"]),
                "ratingaverage":float(entry.find("media:community").find("media:starrating")["average"])
            }
        if(vid==None):
            chanid=addobject("ytvideos",data)
            print(data["title"])
            if sendtel:
                telegram_bot_sendtext(data["title"]+" \n"+"https://www.youtube.com/watch?v="+data["videoid"]+" \n"+data["thumbnail"])
        else:
            #print(vid)
            #print(data)
            pass
        pass
import json
def readfile(path):
    with open(path, 'r') as file:
        return file.read()

     
def readsubsjson(x):
    y = json.loads(x)
    pre = "https://www.youtube.com/channel/"
    for c in y["subscriptions"]:
        if(c["url"].startswith(pre)):
            chanid=c["url"][len(pre):]
            print(chanid)
            try:
                loadchannel(chanid,False)
            except Exception as ex:
                traceback.print_exception(type(ex), ex, ex.__traceback__)
                pass
def chatid(update: Update, _: CallbackContext) -> None:
    """Echo the user message."""
    print(str(update.message.chat_id))
    update.message.reply_text(str(update.message.chat_id) + ": " + 
update.message.text)
def loadall():
    curs=sqlgetall("ytchannel","channelid")
    if curs==None:
        print("cursor is none")
        return
    chans = curs.fetchmany(10)
    while len(chans)>0:
        for chan in chans:
            print(".",end="")
            loadchannel(chan[0])
        chans = curs.fetchmany(10)
import time
if __name__ == "__main__":

    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler('start', hello))
    updater.dispatcher.add_handler(CommandHandler('chatid', chatid))
    #
    # updater.start_polling()
    #updater.idle()
    readsubsjson(readfile("/app/newpipe_subscriptions_202201012143.json"))
    
    while True:
        loadall()
        print("waiting 30 seconds")
        time.sleep(30)
    
    
#UC9-y-6csu5WGm29I7JiwpnA
#UCcTt3O4_IW5gnA0c58eXshg
#UCcTt3O4_IW5gnA0c58eXsh
#UCcTt3O4_IW5gnA0c58eXsh