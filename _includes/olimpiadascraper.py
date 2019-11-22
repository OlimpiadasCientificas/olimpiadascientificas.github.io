#!/usr/bin/env python3
from lxml import html
import requests
import functools
import operator
import datetime
from lxml.html.clean import clean_html

class NewsItem:
    cssClass = "rss-item"
    def __init__(self, title, url, author="", summary="", date=""):
        self.title = title
        self.url = url
        self.author = author
        self.summary = summary
        self.date = date
    def getParsedDate(self):
        if self.date == "":
            return ""
        else:
            return self.date
            
    def toHtml(self):
        date = self.getParsedDate()
        htmlString = f"""<li class="{self.cssClass}"><a href="{self.url}" class="{self.cssClass}">{self.title}</a> <span class="rss-item-auth">{'('+self.author+')' if self.author else ''}</span><br><span class="rss-date">{date}</span><br>{self.summary}</li>"""
        return htmlString
    
    def __str__(self):
        return f"{self.title} {self.url} {self.author} {self.date} {self.summary}"

class NewsOuterContainer:
    cssClass = "rss-box"
    def __init__(self, title, url, innerItems):
        self.title = title
        self.url = url
        self.innerItems = innerItems

    def outerTop(self):
       return  f"""<div class="{self.cssClass}" id="{self.getHtmlID()}"><p class="rss-title">{self.title}</p><ul class="rss-items">"""

    def outerBottom(self):
       return  """</li></ul></div>"""
        
    def toHtml(self):
        innerItemsHtml = [x.toHtml() for x in self.innerItems]
        innerHtml = functools.reduce(operator.add, innerItemsHtml)
        return self.outerTop() + innerHtml + self.outerBottom()
    
    def getHtmlID(self):
        return re.sub("[^\w]", "", f"news{self.title}")
    
    def __str__(self):
        outerText = f"{self.title} {self.url} \n"
        innerItemsText = [str(x) for x in self.innerItems]
        innerText = functools.reduce(lambda a,b: a + "\n" + b, innerItemsText)
        return outerText + innerText
    
#Helper functions
def urlFromA(elementA):
    return elementA.attrib['href']

def itemFromAs(elementAs, prependURL=""):
    items = [NewsItem(x.text, prependURL + x.attrib['href']) for x in elementAs]
    return items

def getDataFromObfPage(page):
    obf = requests.get(page)
    obftree = html.fromstring(obf.content)
    obfoldernewshtml = obftree.xpath('//ul[@class="uk-list"]/li/a')
    obfoldernews =[(x.text, "http://www.sbfisica.org.br"+ x.attrib['href']) for x in obfoldernewshtml]
    
    obfirstnewstitles = [x.strip() for x in obftree.xpath('//h1[@class="uk-article-title"]/text()')]
    obffirstnewsarticles = [x.attrib['data-permalink'] for x in obftree.xpath('//article[@class="uk-article"]')]
    obflatestnews = list(zip(obfirstnewstitles, obffirstnewsarticles)) + obfoldernews
    
    items = [NewsItem(x[0], x[1]) for x in obflatestnews]

    return items

def getDataFromObf():
    links = ['http://www.sbfisica.org.br/v1/olimpiada/2019/index.php/2-uncategorised/',
             'http://www.sbfisica.org.br/v1/olimpiada/2019/index.php/2-uncategorised?start=8']
    items = [getDataFromObfPage(link) for link in links]
    items = functools.reduce(operator.add, items)
    return NewsOuterContainer("OBF", 'http://www.sbfisica.org.br/v1/olimpiada', items)

def getDataFromOba():
    oba = requests.get("http://www.oba.org.br/site/?p=conteudo&pag=conteudo&idconteudo=12&idcat=18&subcat=")
    obatree = html.fromstring(oba.content)
    for br in obatree.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    obanewshtml = obatree.xpath('//span[@class="subtitulocont"]')
    content = obanewshtml[0].getparent().text_content()
    content = re.sub('\n', '<br>\n', content)
    items = [NewsItem(title = "Notícias da OBA", url = "http://www.oba.org.br/site/?p=conteudo&pag=conteudo&idconteudo=12&idcat=18&subcat=", summary = content)]
    return NewsOuterContainer("OBA", 'http://www.oba.org.br/', items)
#    oba = requests.get("http://www.oba.org.br/site/?p=conteudo&pag=conteudo&idcat=17")
#    obatree = html.fromstring(oba.content)
#    obanewshtml = obatree.xpath('//div[@id="lista"]//a')
#    items = itemFromAs(obanewshtml, )
#    return NewsOuterContainer("OBA", 'http://www.oba.org.br/', items)

def getDataFromObc(p):
    """useless"""
    oba = requests.get("http://www.obciencias.com.br/notiacutecias.html")
    obatree = html.fromstring(oba.content)
    obanewshtml = obatree.xpath('//div[@id="lista"]//a')

    
def getDataFromObq():
    "http://www.obquimica.org/noticias/"
import feedparser
def parseFeed(url):
    feed = feedparser.parse(url)
    parseDate = lambda date: datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
    date = lambda entry: parseDate(entry['published'])
    summary = lambda entry: entry['summary']
    author = lambda entry: entry['author']
    title = lambda entry: entry['title']
    url = lambda entry: entry['link']
    newsItem = lambda x: NewsItem(title(x), url(x), author(x), summary(x), date(x))
    items = [newsItem(x) for x in feed['entries']]
    feedTitle = feed.feed.title
    feedUrl = feed.feed.link
    return NewsOuterContainer(feedTitle, feedUrl, items)
    
def getDataFromObm():
    obm = parseFeed("https://www.obm.org.br/rss")
    return obm


import re
def getDataFromNoic():
    noicItems = parseFeed("https://noic.com.br/rss")
    oldToHtml = noicItems.toHtml
    noicItems.toHtml = lambda : re.sub('\\n.*NOIC</a>.</p>', '', oldToHtml())
    return noicItems


class TabbedContainers:
    def __init__(self, containers):
        self.containers = containers
    
    def generateAllHtml(self):
        buttons = self.generateButtons()
        containers = self.generateContainerContents()
        script = self.getScript()
        style = self.getStyle()
        return buttons + containers + script + style
        
    def getButtonIdFromContainer(self, container):
        containerID = container.getHtmlID()
        buttonID = "button" + containerID 
        return buttonID
        
    def generateButton(self, container):
        containerID = container.getHtmlID()
        buttonID = self.getButtonIdFromContainer(container)
        return f"""<button class="tablinks" id="{buttonID}" onclick="openTab('{containerID}', '{buttonID}')">{container.title}</button>"""
    
    def generateButtonsTop(self):
        return """<div class="tab">"""


    def generateButtonBottom(self):
        return """</div>"""
    
    def generateButtons(self):
        containerButtons = [self.generateButton(container) for container in containers]
        containerButtons = functools.reduce(lambda a,b: a + b, containerButtons)
        return self.generateButtonsTop() + containerButtons + self.generateButtonBottom()
    
    def generateContainerContents(self):
        containersContent = [container.toHtml() for container in containers]
        containersContent = functools.reduce(lambda a,b: a + b, containersContent)
        return containersContent
    
    #"based on w3school https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_tabs"
    def getScript(self):
        cssClass = NewsOuterContainer.cssClass
        firstContainer = self.containers[0]
        firstID = firstContainer.getHtmlID()
        firstButtonID = self.getButtonIdFromContainer(firstContainer)
        script = """<script>
function openTab(tabName, buttonName) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("%s");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(tabName).style.display = "block";
  document.getElementById(buttonName).className += " active";
}
openTab('%s','%s')
</script>""" % (cssClass, firstID, firstButtonID)
        return script
    def getStyle(self):
        cssClass = NewsOuterContainer.cssClass
        css = """<style>
/* Style the tab */
.tab {
  overflow: hidden;
  border: 1px solid #ccc;
  background-color: #f1f1f1;
}

/* Style the buttons inside the tab */
.tab button {
  background-color: inherit;
  float: left;
  border: none;
  outline: none;
  cursor: pointer;
  padding: 14px 16px;
  transition: 0.3s;
  font-size: 17px;
}

/* Change background color of buttons on hover */
.tab button:hover {
  background-color: #ddd;
}

/* Create an active/current tablink class */
.tab button.active {
  background-color: #ccc;
}

/* Style the tab content */
.%s {
  display: none;
}
</style>""" % cssClass
        return css
    

if __name__ == "__main__":
    containers = [getDataFromNoic(), getDataFromObm(), getDataFromObf(), getDataFromOba()]

    tabbedContainers = TabbedContainers(containers)

    import sys, os
    directory = os.path.dirname(os.path.abspath(__file__))
    filename = "news.html"
    filepath = os.path.join(directory, filename)
    print("generating "+ filepath)
    f = open(filepath, "w")
    f.write(tabbedContainers.generateAllHtml())
    f.close()
