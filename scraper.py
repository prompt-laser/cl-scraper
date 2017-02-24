#############################################################################################
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
from operator import attrgetter         #used for sorting the results by attribute
from string import digits               #used for parsing the price from the post title

#This is the custom class used for storing information about each post
class posting:

        #This calculates the score of the post based on specified keywords found in the post description.
        def SetScore(self, terms):
                self.score = 0                                          #Set the score to 0 so the score doesn't keep climbing
                if(self.description):                                   #Make sure there's a description before trying to score it
                        for term in terms:                              #For each item in the list of search terms check the description for that term
                                tempDesc = self.description.lower()     #Convert the description to all lowercase text
                                if(tempDesc.find(term) != -1):          #If the term is found
                                        self.score = self.score - 1     #Take one point off the score

        #This figures out the price based on the price listed in the title
        def SetPrice(self, title):
                splitString = title.split(' ')                                                  #Split the string on spaces to hopefully get the price isolated
                for string in splitString:                                                      #Iterate through each word created by splitting the string
                        if(string):                                                             #Make sure there's a value stored in the string
                                if (string[0] == '$'):                                          #If the first character of the word is a $
                                        string = string.replace("$",'')                         #Remove the $
                                        string = ''.join(c for c in string if c in digits)      #Remove all of the letters from the word so you have a string of numbers
                                        self.price = int(string)                                #Set the price to the integer value of the created string

        #This iinitializes a new instance of the class
        def __init__(self, link, desc, title):
                self.link = link                #Set the link property to the passed value
                self.description = desc         #Set the description property to the passed value
                self.title = title              #Set the title property to the passed value
                self.score = 0                  #Set the score to 0
                self.price = 0                  #Set the price to 0

#Open config file and get stored configuration settings
configFile = open("settings")                   #Open config stored in settings
for config in configFile:                       #Iterate through each line of the file
        split = config.split('=')               #Split the line on the equals sign. This allows us to get the setting and its stored value
        split[1] = split[1].replace('\n','')    #Remove the newline character from the end of the string
        if(split[0] == 'doc_root'):             #If the setting is for the web document root
                docRoot = split[1]              #Set the docRoot variable to the stored value
        elif(split[0] == 'search'):             #If the setting is for the search terms
                searchFile = split[1]           #Set the searchFile variable to the stored value
        elif(split[0] == 'cities'):             #If the setting is for the list of URLs
                siteFile = split[1]             #Set the siteFile variable to the stored value
configFile.close()                              #Close the config file

posts = []              #Create the posts list
searchTerms = []        #Create the searchTerms list
urls = []               #Create the URLs list

#Main loop of the script
while(True):

        #Get the list of URLs to search
        urlFile = open(siteFile, 'r')           #Open the URL file
        for site in urlFile:                    #Iterate through each line of the file
                site = site.replace('\n', '')   #Remove the newline character from the end of the string
                urls.append(site)               #Add the URL to the URLs list
        urlFile.close()                         #Close the URL file

        #Get RSS feedd
        for url in urls:                                        #Iterate through the list of URLs
                response = urllib.urlopen(url)                  #Open the link
                payload = response.read()                       #Get the data from the link
                response.close()                                #Close the link

                encoding = chardet.detect(payload)['encoding']  #Detect the encoding of the returned data
                payload = unicode(payload,encoding)             #Re-encode the data in unicode
                payload = payload.encode("utf8")                #Re-encode the data in UTF-8

                xml = ET.fromstring(payload)                    #Parse the data into XML

                #Parse XML into usable data and add it to the posts list
                for child in xml:                                                               #Iterate through the elements of the XML
                        link = child.find('{http://purl.org/rss/1.0/}link').text                #Get the link text
                        description = child.find('{http://purl.org/rss/1.0/}description').text  #Get the description text
                        title = child.find('{http://purl.org/rss/1.0/}title').text              #Get the title text

                        posts.append(posting(link, description, title))                         #Add an element to the posts list. Sending the parsed data to the class constructor

        #Get the search terms
        file = open(searchFile, 'r')                            #Open the file with the search terms in it
        for line in file:                                       #Iterate over each line of the file
                fileString = line                               #Set fileString to the string from file
                fileString = fileString.replace("\n", '')       #Remove the newline character from the end of the string
                searchTerms.append(fileString)                  #Add the term to the list of search terms
        file.close()                                            #Close the search terms file

        #Score and set the price of each post
        for post in posts:                                      #Iterate through the list of posts
                post.title = post.title.replace("&#x0024;","$") #Replace the unicode value with a $
                post.SetScore(searchTerms)                      #Set the score of the post passing the list of search terms
                post.SetPrice(post.title)                       #Set the price of the post passing the title

        posts.sort(key=attrgetter('score', 'price'))            #Sort the posts by score(lowest first), and then by price(lowest first)

        #Write the results to index.html at the document root specified in the config file
        writeFile = open(docRoot + "/index.html", "w")  #Open index.html for writing
        writeFile.write("<html><body>")                 #Write the opening tags

        for post in posts:                                                                                                                                      #Iterate through the list of posts
                print post.title, "\n", post.link, "\n", post.description, "\n", post.score, "\n\n"                                                             #Write post info to console for debugging

                if (post.description):                                                                                                                          #If the post has a description
                        writeFile.write("<br><a href='" + post.link + "'>" + post.title + "</a><br>" + str(post.score) + "<br>" + str(post.price) + "<br><br>") #Write the post information to index.html inserting line breaks into the html

        writeFile.write("</body></html>")       #Write the closing tags

        writeFile.close()                       #Close index.html

        searchTerms = []                        #Empty the list of search terms so we can change them mid stream
        posts = []                              #Empty the list of posts so we don't get duplicates
        urls = []                               #Empty the list of URLs so we don't open the same link multiple times
        
        time.sleep(60)                          #Sleep for 1 minute before doing it all again
