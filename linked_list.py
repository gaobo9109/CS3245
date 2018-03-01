class Node:
  def __init__(self,initdata):
    self.data = initdata
    self.next = None
    self.skip = None

  def getData(self):
    return self.data

  def getNext(self):
    return self.next

  def getSkip(self):
    return self.skip

  def setData(self,newdata):
    self.data = newdata

  def setNext(self,newnext):
    self.next = newnext

  def setSkip(self, skip):
    self.skip = skip

  def hasNext(self):
    return self.next is not None

  def hasSkip(self):
    return self.skip is not None

class LinkedList:
  def __init__(self):
    self.head = None
    self.tail = None
    self.size = 0

  def add(self, item):
    if self.head is None:
      self.head = Node(item)
      self.tail = self.head
    else:
      self.tail.setNext(Node(item))
      self.tail = self.tail.getNext()
    self.size += 1

  def getHead(self):
    return self.head

  def toList(self):
    result = []
    node = self.head

    while node is not None:
      result.append(node.getData())
      node = node.getNext()

    return result


