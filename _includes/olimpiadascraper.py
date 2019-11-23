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
        itemsHtml = [x.toHtml() for x in self.items]
        innerHtml = functools.reduce(operator.add, itemsHtml)
        return self.outerTop() + innerHtml + self.outerBottom()
    
    def getHtmlID(self):
        return re.sub("[^\w]", "", f"news{self.title}")
    
    def __str__(self):
        outerText = f"{self.title} {self.url} \n"
        itemsText = [str(x) for x in self.items]
        innerText = functools.reduce(lambda a,b: a + "\n" + b, itemsText)
        return outerText + innerText
    
#Helper functions
def urlFromA(elementA):
    return elementA.attrib['href']

def elementFromUrl(url):
    page = requests.get(url)
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
    oba = requests.get("http://www.oba.org.br/site/?p=conteudo&pag=conteudo&idconteudo=12&idcat=18&subcat=")
    obatree = html.fromstring(oba.content)
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
    return NewsOuterContainer("OBL", 'http://www.obling.org//', items)



def getDataFromObc(p):
    """useless"""
    "div class landing-banner-inner"
    oba = requests.get("http://www.obciencias.com.br/notiacutecias.html")
    obatree = html.fromstring(oba.content)
    obanewshtml = obatree.xpath('//div[@id="lista"]//a')

    
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
    noicItems.toHtml = lambda : re.sub('\\n.*NOIC</a>.</p>', '', oldToHtml())
    return noicItems

def getDataFromObr():
    obr = parseFeed("http://www.obr.org.br/rss")
    return obr
    
def getDataFromObmep():
    "http://www.obmep.org.br/listarNoticias.DO"

def getDataFromObn():
    obn = parseFeed("http://cienciasecognicao.org/brazilianbrainbee/feed")
    obn.title = "OBN"
    return obn
    
def getDataFromObsma():
    obsma = parseFeed("https://olimpiada.fiocruz.br/rss")
    return obsma
    
def getDataFromIyptBr():
    "a wsite-button-highlight"
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
    


def f(function):
    try:
        return function()
    except:
        return None
    
if __name__ == "__main__":
    containers = [f(getDataFromNoic), f(getDataFromObm), f(getDataFromObf), f(getDataFromOba), f(getDataFromObq), f(getDataFromObi), f(getDataFromOnhb), f(getDataFromObb), f(getDataFromObl), f(getDataFromObn), f(getDataFromObr),  f(getDataFromObsma)]
    tabbedContainers = TabbedContainers(containers)
    text = tabbedContainers.generateAllHtml()

    import sys, os
    directory = os.path.dirname(os.path.abspath(__file__))
    filename = "news.html"
    filepath = os.path.join(directory, filename)
    print("generating "+ filepath)
    f = open(filepath, "w")
    f.write(text)
    f.close()
