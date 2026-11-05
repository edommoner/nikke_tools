"""Observe the original CPython integer RNG;never used as GPU input."""
import random
class Observer(random.Random):
 def __init__(self,seed):self.draws=0;self.rejects=0;self.samples=0;super().__init__(seed)
 def getrandbits(self,k):
  self.draws+=int(k!=0);return super().getrandbits(k)
 def _randbelow(self,n):
  start=self.draws;value=random.Random._randbelow_with_getrandbits(self,n);self.rejects+=self.draws-start-1;return value

