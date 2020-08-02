#!/usr/bin/env python3
from lxml import html
import requests
import functools
import operator
import datetime
from lxml.html.clean import clean_html
from lxml import etree
#import pickle
import dill
import sys, os

class NewsItem:
    cssClass = "rss-item"
    def __init__(self, title, url, author="", summary="", date=""):
        self.title = title
        self.url = url
        self.author = author
        self.summary = summary
        self.date = date
        
    def getParsedDate(self):
        if isinstance(self.date, str):
            return self.date
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

    def summaryText(self):
        document = html.document_fromstring(self.summary)
        return "\n".join(etree.XPath("//text()")(document))

    def toText(self):
        document = html.document_fromstring(self.summary)
        text =  "\n".join(etree.XPath("//text()")(document))
        return f"{self.title}\n {self.url} \n {text} \n by {self.author} {self.date} "
    def __eq__(self, other):
        return (self.title == other.title and self.url==other.url and self.author==other.author and self.summary==other.summary and self.date==other.date)

class NewsOuterContainer:
    cssClass = "rss-box"
    def __init__(self, title, url, items):
        self.title = title
        self.url = url
        self.items = items

    def outerTop(self):
       return  f"""<div class="{self.cssClass}" id="{self.getHtmlID()}"><p class="rss-title"><a href="{self.url}">{self.title}</a></p><ul class="rss-items">"""

    def outerBottom(self):
       return  """</li></ul></div>"""
        
    def toHtml(self):
        print("converting" + self.title)
        itemsHtml = [x.toHtml() for x in self.items]
        innerHtml = functools.reduce(operator.add, itemsHtml)
        return self.outerTop() + innerHtml + self.outerBottom()
    
    def getHtmlID(self):
        return re.sub("[^\w]", "", f"news{self.title}")

    def cleanHtml(self, func):
        for item in self.items:
            item.summary = func(item.summary)
    
    def __str__(self):
        outerText = f"{self.title} {self.url} \n"
        itemsText = [str(x) for x in self.items]
        innerText = functools.reduce(lambda a,b: a + "\n" + b, itemsText)
        return outerText + innerText
    
#Helper functions
def urlFromA(elementA):
    return elementA.attrib['href']

def elementFromUrl(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
    page = requests.get(url, headers=headers)
    element = html.fromstring(page.content)
    return element 

def itemFromAs(elementAs, baseref=""):
    if elementAs:
        for br in elementAs[0].xpath("//br"):
            br.tail = " " + br.tail if br.tail else " "
            
    for item in elementAs:
        if baseref:
            item.make_links_absolute(baseref)


    items = [NewsItem(x.text_content(), x.attrib['href']) for x in elementAs]
    return items

from lxml import etree
def outerHtml(element, baseref=""):
    """make_links_absolute(base_href, resolve_base_href=True):

    This makes all links in the document absolute, assuming that base_href is the URL of the document. So if you pass base_href="http://localhost/foo/bar.html" and there is a link to baz.html that will be rewritten as http://localhost/foo/baz.html."""
    if baseref:
        element.make_links_absolute(baseref)
    for tag in element.xpath('//*[@class]'):
        # For each element with a class attribute, remove that class attribute
        tag.attrib.pop('class')
    etree.strip_elements(element, ['img'])
    return clean_html(etree.tostring(element, pretty_print=True, encoding='unicode'))

def getDataFromObfPage(page):
    obftree = elementFromUrl(page)
    obfoldernewshtml = obftree.xpath('//ul[@class="uk-list"]/li/a')
    obfoldernews =[(x.text, "http://www.sbfisica.org.br"+ x.attrib['href']) for x in obfoldernewshtml]
    
    obfirstnewstitles = [x.strip() for x in obftree.xpath('//h1[@class="uk-article-title"]/text()')]
    obffirstnewsarticles = [x.attrib['data-permalink'] for x in obftree.xpath('//article[@class="uk-article"]')]
    obflatestnews = list(zip(obfirstnewstitles, obffirstnewsarticles)) + obfoldernews
    
    items = [NewsItem(x[0], x[1]) for x in obflatestnews]

    return items

def getDataFromObf():
    links = ['http://www.sbfisica.org.br/v1/olimpiada/2020/index.php/2-uncategorised/',
             'http://www.sbfisica.org.br/v1/olimpiada/2020/index.php/2-uncategorised?start=8']
    items = [getDataFromObfPage(link) for link in links]
    items = functools.reduce(operator.add, items)
    return NewsOuterContainer("OBF", 'http://www.sbfisica.org.br/v1/olimpiada', items)

def getDataFromObi():
    obi = elementFromUrl('https://olimpiada.ic.unicamp.br/')
    content = obi.xpath('//div[@class="copy-banner"]//a')
    items = itemFromAs(content, 'https://olimpiada.ic.unicamp.br/')
    container = NewsOuterContainer(title = "OBI", url = 'https://olimpiada.ic.unicamp.br/', items = items)
    return container

def getDataFromOnhb():
    links = ["https://www.olimpiadadehistoria.com.br/noticias/index?CFP=0&ONHB=1", "https://www.olimpiadadehistoria.com.br/noticias/index/page:2?CFP=0&ONHB=1", "https://www.olimpiadadehistoria.com.br/noticias/index/page:3?CFP=0&ONHB=1"]
    onhbs =  map(lambda x: elementFromUrl(x), links) 
    contents = map(lambda x: x.xpath('//a[@class="link_limpo"]'), onhbs)
    itemss = map(lambda x: itemFromAs(x, 'https://www.olimpiadadehistoria.com.br/'), contents)
    items = functools.reduce(operator.add, itemss)
    container = NewsOuterContainer(title = "ONHB", url = 'https://www.olimpiadadehistoria.com.br/', items = items)
    return container

def getDataFromOba():
    obatree = elementFromUrl("http://www.oba.org.br/site/?p=conteudo&pag=conteudo&idconteudo=12&idcat=18&subcat=")
    obanewshtml = obatree.xpath('//span[@class="subtitulocont"]')
    obanewshtml = obanewshtml[0].getparent()
    content = outerHtml(obanewshtml, "http://www.oba.org.br/site/")
    items = [NewsItem(title = "Notícias da OBA", url = "http://www.oba.org.br/site/?p=conteudo&pag=conteudo&idconteudo=12&idcat=18&subcat=", summary = content)]
    return NewsOuterContainer("OBA", 'http://www.oba.org.br/', items)

def getDataFromObb():
    provas = elementFromUrl("http://olimpiadasdebiologia.butantan.gov.br/provas-e-gabaritos-e-classificacoes")
    provasdiv = provas.xpath('//div[@class="element0inOrder0"]')[0]
    provascontent = outerHtml(provasdiv, "http://olimpiadasdebiologia.butantan.gov.br/")
    provasItem =NewsItem(title = "Provas", url = "http://olimpiadasdebiologia.butantan.gov.br/provas-e-gabaritos-e-classificacoes", summary = provascontent)

    fases = elementFromUrl("http://olimpiadasdebiologia.butantan.gov.br/fases")
    fasesdiv = fases.xpath('//div[@class="element0inOrder0"]')[0]
    fasescontent = outerHtml(fasesdiv, "http://olimpiadasdebiologia.butantan.gov.br/")
    fasesItem =NewsItem(title = "Fases", url = "http://olimpiadasdebiologia.butantan.gov.br/fases", summary = fasescontent)

    
    insc = elementFromUrl("http://olimpiadasdebiologia.butantan.gov.br/inscricoes-e-regulamentos")
    inscdiv = insc.xpath('//div[@class="element0inOrder1"]')[0]
    insccontent = outerHtml(inscdiv, "http://olimpiadasdebiologia.butantan.gov.br/")
    inscItem =NewsItem(title = "Inscrições", url = "http://olimpiadasdebiologia.butantan.gov.br/inscricoes-e-regulamentos", summary = insccontent)

    items = [provasItem, fasesItem, inscItem]
    
    return NewsOuterContainer("OBB", 'http://olimpiadasdebiologia.butantan.gov.br/', items)

def getDataFromObl():
    obl = elementFromUrl("http://www.obling.org/")
    obldiv = obl.xpath('//div[@id="how"]')[0]
    content = outerHtml(obldiv, "http://www.obling.org/")
    items = [NewsItem(title = "Linha do tempo da OBL", url = "http://www.obling.org/", summary = content)]
    return NewsOuterContainer("OBL", 'http://www.obling.org/', items)



def getDataFromObc():
    "div class landing-banner-inner"
    obc = elementFromUrl("http://www.obciencias.com.br/")
    obchtml = obc.xpath('//div[@class="landing-banner-inner"]')[0]
    obccontent = outerHtml(obchtml, "http://www.obciencias.com.br/")
    obcItem =NewsItem(title = "OBC", url = "http://www.obciencias.com.br/", summary = obccontent)
    return NewsOuterContainer("OBC", 'http://www.obciencias.com.br/', [obcItem])


    
def getDataFromObq():
    "http://www.obquimica.org/noticias/"
    number = 20
    obq = requests.get("http://www.obquimica.org/noticias/")
    obqtree = html.fromstring(obq.content)
    parseDate = lambda date: datetime.datetime.strptime(date, '%d/%m/%Y')
    dates = obqtree.xpath('//i[@class="fa fa-calendar"]')
    newestDates = dates[:number]
    newestDates = [date.getparent().text_content()[1:] for date in newestDates]
    newestDates = [parseDate(d) for d in newestDates]
    news = obqtree.xpath('//div[@class="post-text"]/a')
    newestNews = news[:number]
    urls = [urlFromA(n) for n in newestNews]
    titles = [a.getchildren()[0].text for a in newestNews]
    
    authors = obqtree.xpath('//div[@class="post-site-info"]')[:number]
    authors = [author.text_content().strip() for author in authors]
    
    data = zip(titles, urls, newestDates, authors)
    newsItem = lambda x: NewsItem(title = x[0], url = x[1], author = x[3], summary = "", date = x[2])
    items = [newsItem(x) for x in data]
    return NewsOuterContainer("OBQ", 'http://www.obquimica.org/noticias/', items)
    
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
    noicItems.cleanHtml(lambda text : re.sub('\\n.*NOIC</a>.</p>', '', text))
    return noicItems

def getDataFromObr():
    obr = parseFeed("http://www.obr.org.br/rss")
    return obr


def getDataFromObn():
    obn = parseFeed("http://www.cienciasecognicao.org/portal/?feed=rss2")
    obn.title = "Brain Bee"
    return obn
    
def getDataFromObsma():
    obsma = parseFeed("https://olimpiada.fiocruz.br/rss")
    obsma.title = "OBSMA"
    return obsma

def getDataFromObfep():
    obfep = parseFeed("http://www.sbfisica.org.br/~obfep/rss")
    obfep.title = "OBFEP"
    return obfep
    
def getDataFromObg():
    """Page generated by javascript, so not possible to scrape."""
    obg = elementFromUrl("https://obgeografia.org/#/novidades")
    obghtml = obg.xpath('//div[@class="news-item"]//a')
    items = itemFromAs(obghtml, "https://obgeografia.org/#/novidades")
    return NewsOuterContainer("OBG", 'https://obgeografia.org/', items)
    
def getDataFromObmep():
    number = 25
    content = elementFromUrl("http://www.obmep.org.br/listarNoticias.DO")
    obmephtml = content.xpath('//ul[@id="internalNewsList"]//a')
    items = itemFromAs(obmephtml, "http://www.obmep.org.br/listarNoticias.DO")
    items = items[:number]
    return NewsOuterContainer("OBMEP", 'http://www.obmep.org.br/', items)

def getDataFromIyptBr():
    iypt = elementFromUrl("http://www.iypt.com.br/")
    iypthtml = iypt.cssselect('a.wsite-button')
    iyptitems = itemFromAs(iypthtml, "http://www.iypt.com.br/")
    return NewsOuterContainer("IYPTBr", 'http://www.iypt.com.br/', iyptitems)
class TabbedContainers:
    def __init__(self, containers):
        self.containers = [container for container in containers if container] #Ignore empty things
    
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
        containerButtons = [self.generateButton(container) for container in self.containers]
        containerButtons = functools.reduce(lambda a,b: a + b, containerButtons)
        return self.generateButtonsTop() + containerButtons + self.generateButtonBottom()
    
    def generateContainerContents(self):
        containersContent = [container.toHtml() for container in self.containers]
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

</style>""" 
        return css
    


def f(function):
    try:
        return function()
    except:
        return None


def getAllNews(listOfContainers):
    news = []
    for container in listOfContainers:
        for item in container.items:
            news.append(item)
    return news


def postRecentNewsToFB(newss):
    import facebook
    print(newss)
    with open('token', 'r') as file:
        token = file.read().replace('\n', '')
    graph = facebook.GraphAPI(access_token=token, version="3.0")
    for news in newss[:1]:
        graph.put_object(
          parent_object=273791905985831,
          connection_name="feed",
          message= f"{news.title} \n {news.summaryText()} \npor: {news.author} \n  {news.date}",
          link=news.url
        )
def main():
    directory = os.path.dirname(os.path.abspath(__file__))
    containers = [f(getDataFromNoic), f(getDataFromObm), f(getDataFromObf), f(getDataFromOba), f(getDataFromObq), f(getDataFromObi), f(getDataFromOnhb), f(getDataFromObb), f(getDataFromObl), f(getDataFromObn), f(getDataFromObr),  f(getDataFromObsma), f(getDataFromObc), f(getDataFromIyptBr), f(getDataFromObmep), f(getDataFromObfep)]
    #containers = [f(getDataFromNoic), f(getDataFromObm)]
    maxNewNews = 20
    try:
        with open(os.path.join(directory,'previousnews.b'), 'r+b') as previousNewsFile:
            previousContainers = dill.load(previousNewsFile)
            fullContainers = [containers[i] or previousContainers[i] for i in range(len(containers))]
    except:
        fullContainers = containers
        previousContainers = []
    with open(os.path.join(directory,'previousnews.b'), 'w+b') as previousNewsFile:
        dill.dump(fullContainers, previousNewsFile)

    allNews = getAllNews([container for container in fullContainers if container])
    allPreviousNews = getAllNews([container for container in previousContainers if container])
    allNewNews = [x for x in allNews if x not in allPreviousNews]
    try:
        with open(os.path.join(directory,'recentnews.b'), 'r+b') as recentNewsFile:
            recentNews = allNewNews + dill.load(recentNewsFile)
            recentNews =  recentNews[:maxNewNews]
    except:
        recentNews = allNewNews
        recentNews =  recentNews[:maxNewNews]
    with open(os.path.join(directory,'recentnews.b'), 'w+b') as recentNewsFile:
        dill.dump(recentNews, recentNewsFile)

    recentNewsContainer = NewsOuterContainer("Novidades", '#', recentNews)
    
    tabbedContainers = TabbedContainers(fullContainers)
    text = tabbedContainers.generateAllHtml()
    
    try:
        filename = "news.html"
        filepath = os.path.join(directory, filename)
        print("generating "+ filepath)
        thisfile = open(filepath, "w")
        thisfile.write(text)
        thisfile.close()
    except:
        print("Could not open file")
    postRecentNewsToFB(allNewNews)
if __name__ == "__main__":
    main()

