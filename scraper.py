import urllib
import xml.etree.ElementTree as ET
import chardet
import time
from operator import attrgetter
from string import digits

class posting:

        def SetScore(self, terms):
                self.score = 0
                if(self.description):
                        for term in terms:
                                tempDesc = self.description.lower()
                                if(tempDesc.find(term) != -1):
                                        self.score = self.score - 1

        def SetPrice(self, title):
                splitString = title.split(' ')
                for string in splitString:
                        if(string):
                                if (string[0] == '$'):
                                        string = string.replace("$",'')
                                        self.price = ''.join(c for c in string if c in digits)

        def __init__(self, link, desc, title):
                self.link = link
                self.description = desc
                self.title = title
                self.score = 0
                self.price = 0

urls = {"https://sheboygan.craigslist.org/search/sya?format=rss", "https://milwaukee.craigslist.org/search/sya?format=rss", "https://appleton.craigslist.org/search/sya?format=rss", "http://greenbay.craigslist.org/search/sya?format=rss"}
posts = []
searchTerms = []

while(True):

        for url in urls:
                response = urllib.urlopen(url)
                payload = response.read()
                response.close()

                encoding = chardet.detect(payload)['encoding']
                payload = unicode(payload,encoding)
                payload = payload.encode("utf8")

                xml = ET.fromstring(payload)

                for child in xml:
                        tempLink = child.find('{http://purl.org/rss/1.0/}link').text

                        posts.append(posting(tempLink, child.find('{http://purl.org/rss/1.0/}description').text, child.find('{http://purl.org/rss/1.0/}title').text))

        file = open('searchTerms', 'r')
        for line in file:
                fileString = line
                fileString = fileString.replace("\n", '')
                searchTerms.append(fileString)
        file.close()

        for post in posts:
                post.title = post.title.replace("&#x0024;","$")
                post.SetScore(searchTerms)
                post.SetPrice(post.title)

        posts.sort(key=attrgetter('score', 'price'))

        writeFile = open("/var/www/html/index.html", "w")

        writeFile.write("<html><body>")

        for post in posts:
                print post.title, "\n", post.link, "\n", post.description, "\n", post.score, "\n\n"

                if (post.description):
                        writeFile.write("<br><a href='" + post.link + "'>" + post.title + "</a><br>" + str(post.score) + "<br>" + str(post.price) + "<br><br>")

        writeFile.write("</body></html>")

        writeFile.close()

        searchTerms = []
        posts = []

        time.sleep(60)