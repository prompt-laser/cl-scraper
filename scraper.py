############################################################################################
#Craigslist scraper
#
#This script will scrape the rss feeds for a category and rank the posts based on how many
#keyword matches there are in the description. The scoring function takes points off for
#matches so we can sort the posts in ascending order by score and price. The lower the score,
#the better the post.
#
#Created By: prompt-laser
#############################################################################################

import urllib                           #used for getting the XML from craigslist
import xml.etree.ElementTree as ET      #used to parse the XML into usable data
import chardet                          #used to make sure the XML is in a parsable format
import time                             #used to sleep the script during the main while loop
import sys                              #used for exiting the script on errors
import sqlite3                          #used for database access
from operator import attrgetter         #used for sorting the results by attribute
from string import digits               #used for parsing the price from the post title

class SearchTerm:

        def __init__(self, search):
                splitString = search.split('=')
                try:
                        self.value = int(splitString[1])
                        self.term = splitString[0]
                except:
                        self.value = 1
                        self.term = splitString[0]

#This is the custom class used for storing information about each post
class posting:

        #This calculates the score of the post based on specified keywords found in the post description.
        def SetScore(self, terms, min, max):
                self.score = 0                                                  #Set the score to 0 so the score doesn't keep climbing
                if(self.description):                                           #Make sure there's a description before trying to score it
                        for term in terms:                                      #For each item in the list of search terms check the description for that term
                                tempDesc = self.description.lower()             #Convert the description to all lowercase text
                                if(tempDesc.find(term.term) != -1):             #If the term is found
                                        self.score = self.score - term.value    #Take one point off the score
                if(self.price):                                                 #Make sure there's a value for price
                        if(self.price >= min and self.price <= max):            #If the price is above the minPrice and below the maxPrice
                                self.score = self.score - 1                     #Take one point off the score

        #This figures out the price based on the price listed in the title
        def SetPrice(self, title):
                splitString = title.split(' ')                                                  #Split the string on spaces to hopefully get the price isolated
                for string in splitString:                                                      #Iterate through each word created by splitting the string
                        if(string):                                                             #Make sure there's a value stored in the string
                                if (string[0] == '$'):                                          #If the first character of the word is a $
                                        string = string.replace("$",'')                         #Remove the $
                                        string = ''.join(c for c in string if c in digits)      #Remove all of the letters from the word so you have a string of numbers
                                        try:                                                    #Wrap setting the price in a try statement. This step errored out in testing
                                                self.price = int(string)                        #Set the price to the integer value of the created string
                                        except:                                                 #If there's an error
                                                self.price = 0                                  #Set the price to 0

        #This iinitializes a new instance of the class
        def __init__(self, link, desc, title, price, score):
                self.link = link                #Set the link property to the passed value
                self.description = desc         #Set the description property to the passed value
                self.title = title              #Set the title property to the passed value
                self.score = 0                  #Set the score to 0
                self.price = 0                  #Set the price to 0
                if(price):
                        self.price = price
                if(score):
                        self.score = score

#Open the database
conn = sqlite3.connect('CraigsListPosts.db')
c = conn.cursor()

#Try to create the table. This will error out if the table already exists.
try:
        c.execute('''CREATE TABLE posts
                        (title text, url text, description text, price integer, score integer, month text)''')
except:
        print('Database already exists')


#Open config file and get stored configuration settings
print("Loading saved settings")                 #Output to let the user know it's working
configFile = open("settings")                   #Open config stored in settings

try:                                                    #Wrapping loading of settings in a try statement in case there's an error parsing the min/max price to an integer
        for config in configFile:                       #Iterate through each line of the file
                config = config.replace('\n', '')       #Remove the newline character from th eend of the string
                split = config.split('=')               #Split the line on the equals sign. This allows us to get the setting and its stored value
                if(split[0] == 'doc_root'):             #If the setting is for the web document root
                        docRoot = split[1]              #Set the docRoot variable to the stored value
                elif(split[0] == 'search'):             #If the setting is for the search terms
                        searchFile = split[1]           #Set the searchFile variable to the stored value
                elif(split[0] == 'cities'):             #If the setting is for the list of URLs
                        siteFile = split[1]             #Set the siteFile variable to the stored value
                elif(split[0] == 'min_price'):          #If the setting is for the minimum price
                        minPrice = int(split[1])        #Set the minPrice to the integer value of the setting
                elif(split[0] == 'max_price'):          #If the setting is for the maximum price
                        maxPrice = int(split[1])        #Set the maxPrice to the integer value of the setting
                elif(split[0] == 'doc'):
                        document = split[1]

except:                                                 #If something errors out
        configFile.close()                              #Close the config file
        sys.exit("Error loading settings")              #And exit the script

configFile.close()                                      #Close the config file


posts = []              #Create the posts list
searchTerms = []        #Create the searchTerms list
urls = []               #Create the URLs list

#Main loop of the script
while(True):

        curMonth = time.strftime("%m")
        if(curMonth == "01"):
                oldMonth = ("09",)
        elif(curMonth == "02"):
                oldMonth = ("10",)
        elif(curMonth == "03"):
                oldMonth = ("11",)
        elif(curMonth == "04"):
                oldMonth = ("12",)
        elif(curMonth == "05"):
                oldMonth = ("01",)
        elif(curMonth == "06"):
                oldMonth = ("02",)
        elif(curMonth == "07"):
                oldMonth = ("03",)
        elif(curMonth == "08"):
                oldMonth = ("04",)
        elif(curMonth == "09"):
                oldMonth = ("05",)
        elif(curMonth == "10"):
                oldMonth = ("06",)
        elif(curMonth == "11"):
                oldMonth = ("07",)
        elif(curMonth == "12"):
                oldMonth = ("08",)

        c.execute("DELETE FROM posts WHERE month=?",oldMonth)

        
        try:                                            #Wrap the getting the URLs in a try statement in case the file path is wrong

                #Get the list of URLs to search
                urlFile = open(siteFile, 'r')           #Open the URL file
                for site in urlFile:                    #Iterate through each line of the file
                        site = site.replace('\n', '')   #Remove the newline character from the end of the string
                        urls.append(site)               #Add the URL to the URLs list
                urlFile.close()                         #Close the URL file

        except:                                         #If there's an error opening URL file
                sys.exit("Error reading URL file")      #Exit the script showing an error

        newItems = 0
                
        print("Getting RSS feeds")                      #Output to let the user know it's working

        #Get RSS feed
        for url in urls:                                                #Iterate through the list of URLs

                try:                                                    #Wrap the open RSS feed in a try statement in case a link fails to open
                        response = urllib.urlopen(url)                  #Open the link
                        payload = response.read()                       #Get the data from the link
                        response.close()                                #Close the link

                        encoding = chardet.detect(payload)['encoding']  #Detect the encoding of the returned data
                        payload = unicode(payload,encoding)             #Re-encode the data in unicode
                        payload = payload.encode("utf8")                #Re-encode the data in UTF-8

                        xml = ET.fromstring(payload)                    #Parse the data into XML

                except:                                                 #If there's an error opening/parsing an RSS feed
                        print("Error opening/parsing RSS feed" + url)   #Print an error to let the user know an RSS feed failed to open
                        break

                #Parse XML into usable data and add it to the posts list
                for child in xml:                                                               #Iterate through the elements of the XML
                        link = child.find('{http://purl.org/rss/1.0/}link').text                #Get the link text
                        description = child.find('{http://purl.org/rss/1.0/}description').text  #Get the description text
                        title = child.find('{http://purl.org/rss/1.0/}title').text              #Get the title text

                        query = (link,)

                        c.execute("SELECT * FROM posts WHERE url=?", query)
                        existing = c.fetchone()
                        if(existing == None):
                                newItems = newItems + 1
                                tempPost = posting(link, description, title, 0, 0)
                                tempPost.title = tempPost.title.replace("&#x0024;","$")
                                tempPost.SetPrice(tempPost.title)
                                c.execute("""INSERT INTO posts(title, url, description, price, score, month) VALUES
                                                (?, ?, ?, ?, ?, ?)""",
                                                (tempPost.title, tempPost.link, tempPost.description, tempPost.price, tempPost.score, time.strftime("%m")))
                                conn.commit()
                                
        print("Added " + str(newItems) + " items to the database")

        for row in c.execute("SELECT * FROM posts"):
                posts.append(posting(row[1], row[2], row[0], row[3], row[4]))

        #Get the search terms
        try:                                                            #Wrap the opening search terms file in a try statement in case the path is wrong
                file = open(searchFile, 'r')                            #Open the file with the search terms in it
                for line in file:                                       #Iterate over each line of the file
                        fileString = line                               #Set fileString to the string from file
                        fileString = fileString.replace("\n", '')       #Remove the newline character from the end of the string
                        searchTerms.append(SearchTerm(fileString))      #Add the term to the list of search terms
                file.close()                                            #Close the search terms file
        except:                                                         #If there's an error opening/reading the file
                sys.exit("Error opening/reading file for search terms") #Exit the script showing an error

        for post in posts:
                post.SetScore(searchTerms, minPrice, maxPrice)          #Set the score based on keywords in the description and price

        posts.sort(key=attrgetter('score', 'price'))            #Sort the posts by score(lowest first), and then by price(lowest first)

        #Write the results to index.html at the document root specified in the config file
        print("Writing index.html")                                                     #Output to let the user know what it's doing
        writeFile = open(docRoot + document, "w")                                       #Open index.html for writing
        writeFile.write("<html><head>")                                                 #Write the opening HTML tags
        writeFile.write("<meta http-equiv='refresh' content='121; url=index.html' />")  #Write HTML redirect to refresh the page
        writeFile.write("</head><body><table style='width:100%' border=#000000>")       #Close the head section and declare a html table
        writeFile.write("<tr><th>Item</th><th>Score</th><th>Price</th></tr>")           #Write the column names at the top of the table

        for post in posts:                                      #Iterate through the list of posts
                if (post.description):                          #If the post has a description
                        try:                                    #Wrapping the writing of index.html in a try statement in case something can't be encoded to ascii
                                writeFile.write("<tr><td><a href='" + post.link + "'>" + post.title + "</a></td><td>" + str(post.score) + "</td><td>$" + str(post.price) + "</td></tr>")#Write the post information to index.html inserting $
                        except:                                 #If there's an error
                                writeFile.write("<tr><td><a href='" + post.link + "'>Error writing post title" + "</a></td><td>" + str(post.score) + "</td><td>$" + str(post.price) + "</td></tr>")    #Write the post information minus the$

        writeFile.write("</table></body></html>")       #Write the closing tags

        writeFile.close()                               #Close index.html


        searchTerms = []                                #Empty the list of search terms so we can change them mid stream
        posts = []                                      #Empty the list of posts so we don't get duplicates
        urls = []                                       #Empty the list of URLs so we don't open the same link multiple times

        print("Sleeping for 1 hour")                #Output to let the user know what it's doing
        time.sleep(3600)                                  #Sleep for 1 minute before doing it all again
