import fdb
import httplib2
from BeautifulSoup import BeautifulSoup, SoupStrainer

http = httplib2.Http()

fdb.api_version(200)
# db is an instance of class fdb.Database
db = fdb.open()
# This subspace will have urls for keys, and a list of outbound links for values
pages = fdb.directory.create_or_open(db, ('pages',))
# ranks subspace will have urls for keys, and floating point numbers for values
ranks = pages.create_or_open(db, ('ranks',))


class Page:
  def __init__(self, a):
    self.address = a
    self.score = 0
    self.links = []
    try:
      # Try getting all links associated with address a
      status, self.page = http.request(a)
      for link in filter(lambda l: str(l)[0] is not '#', BeautifulSoup(self.page, parseOnlyThese=SoupStrainer("a"))):
        print a + ' Links to page: '  + link['href']
        # These links should probably get cleaned
        self.links.append(link['href'])
    except:
      print 'Failed on link: ' + a
  
  def dirtySubpages(self):
    return self.links

  # encodable as values in fdb
  def cleanSubpages(self):
    return map(lambda t : t.encode('ascii', errors='backslashreplace'), self.links)
  
  def key(self):
    return str(self.address.encode('ascii', errors='backslashreplace'))

  # All we care to store are the outbound links from the page
  def value(self):
    return str(self.cleanSubpages())
    

class PageRanks:
  def scan(self, startPage='tufts.edu', depth=3):
    self.start = startPage
    self.root = startPage.replace('http://wwww.', '')
    self.scanPage(self.root, depth)

  def scanPage(self, currentPage, remainingDepth=0):
    if currentPage[0] is '/': currentPage.prepend(self.start)
    page = Page(currentPage)
    db[pages[page.key()]] = page.value() 
    if remainingDepth > 0:
      # recurse on links with the same root url
      for p in set(filter(lambda t : self.root in str(t), page.dirtySubpages())):
        self.scanPage(p, remainingDepth - 1)

  def initRanks(self):
    ps = []
    for k in pages:
      v = db[pages[k]]
      print str(v)
      ps.append(k)
    num_pages = len(ps)
    for p in ps:
      db[ranks[p]] = bytes(1/num_pages)
      print 'rank of page ' + p + ' = ' + str(1/num_pages)

  # Can't actually test this cause I'm stuck above
  def computeRanks(self, depth=10):
    for i in range(depth):
      # can't permute old ranks while computing new ranks, so use a temp
      newranks = dict()
      for k, v in pages:
        # Give the current rank of this page away to others in the network
        rank = ranks[k]
        # somehow get the links out of the v from the pages namespace???
        good_links = filter(lambda t : self.root in str(t), v.split(','))      
        for l in good_links:
          #Adjust ranks
          if l in newranks:
            newranks[l] = newranks[l] + (rank / len(good_links))
          else newranks[l] = rank / len(good_lings)
      for k, v in newranks.iteritems():
        ranks[k] = v

pr = PageRanks()
pr.scan('http://www.tufts.edu', 1)
print 'Done scanning'
pr.initRanks()
