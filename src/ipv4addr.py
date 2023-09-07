'''IP calculation functions

- Original by Kailash Joshi.
- Source: https://github.com/kailashjoshi/Ipcalculator/
'''
import sys

def _dec_to_binary(ip_address):
  return list(map(lambda x: bin(x)[2:].zfill(8), ip_address))


def _negation_mask(net_mask):
  wild = list()
  for i in net_mask:
    wild.append(255 - int(i))
  return wild


class IPv4Address(object):
  '''IPCalculator object
  
  Performs miscellaneous calculations on IPv4 addresses
  
  :param str ip_address: IP address
  :param int cidr: CIDR subnet mask length
  '''
  def __init__(self, ip_address, cdir=24):
    if '/' in ip_address:
      self._address_val, self._cidr = ip_address.split('/')
      self._address = list(map(int, self._address_val.split('.')))
    else:
      self._address = list(map(int, ip_address.split('.')))
      self._cidr = cdir

    # Handle other number formats
    if len(self._address) > 4:
      self._address = self._address[:4]
    elif len(self._address) < 4:
      num = self._address.pop()
      while len(self._address) < 4: self._address.append(0)
      i = 3
      while num > 0 and i >= 0:
        self._address[i] = num % 256
        num = num >> 8
        i -= 1

    self.mask = [0, 0, 0, 0]
    for i in range(int(self._cidr)):
        self.mask[int(i / 8)] += 1 << (7 - i % 8)
    self.binary_IP = _dec_to_binary(self._address)
    self.binary_Mask = _dec_to_binary(self.mask)
    self.negation_Mask = _dec_to_binary(_negation_mask(self.mask))

    network = list()
    for x, y in zip(self.binary_IP, self.binary_Mask):
      network.append(int(x, 2) & int(y, 2))
    self.network = network

    broadcast = list()
    for x, y in zip(self.binary_IP, self.negation_Mask):
        broadcast.append(int(x, 2) | int(y, 2))
    self.broadcast = broadcast

  def __str__(self):
    '''human-readable, or informal, string representation of address'''
    return 'IPv4({addr}/{cidr})'.format(addr = ".".join(map(str, self._address)), cidr = self._cidr)

  def net_mask(self):
    '''Return netmask representation
    
    :returns str: string showing the netmask of object
    '''
    return '.'.join(map(str,self.mask))

  def network_ip(self):
    '''Returns the network IP
    
    :returns str: network IP'''
    return '.'.join(map(str,self.network))

  def broadcast_ip(self):
    '''Returns broadcast IP address
    
    :returns str: broadcast IP address'''
    return '.'.join(map(str,self.broadcast))

  def host_range(self):
    '''Host range
    
    :returns str,str: strings with initial to last IP address'''
    min_range = list(self.network)
    min_range[-1] += 1
    max_range = list(self.broadcast)
    max_range[-1] -= 1
    return ".".join(map(str, min_range)), ".".join(map(str, max_range))

  def number_of_host(self):
    '''Calculate the max number of hosts in this IP subnet
    
    :returns int: count of max hosts'''
    return (2 ** sum(map(lambda x: sum(c == '1' for c in x), self.negation_Mask))) - 2

  def host_ip(self, ipoff):
    '''Calculate a host IP in range
    
    :returns str: IP address of host:
    '''
    if ipoff < 0 or ipoff > self.number_of_host():
      raise ValueError('Must be greater than 0 and less than {}'.format(self.number_of_host()))
    address = list(self.network)
    octet = 3
    while ipoff > 0:
      address[octet] += ipoff
      if address[octet] < 256: break
      address[octet] = address[octet] % 256
      ipoff = ipoff >> 8
      octet -= 1
    
    return '.'.join(map(str,address))

  def prefix(self):
    '''Return prefix size
    
    :returns int: number of bits in prefix
    '''
    return int(self._cidr)

if __name__ == '__main__':
  ip = sys.argv[1] if len(sys.argv) > 1 else sys.exit(0)
  ip = IPv4Address(ip)
  # ~ ip.t()
  print('Calculation for: {}'.format(ip))
  print('Prefix: {}'.format(ip.prefix()))
  print('Netmask: {}'.format(ip.net_mask()))
  print('Network ID: {}'.format(ip.network_ip()))
  print('Broadcast address: {}'.format(ip.broadcast_ip()))
  print("Host range: {}".format(ip.host_range()))
  print('Max number of hosts: {}'.format(ip.number_of_host()))
