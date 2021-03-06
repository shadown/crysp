# -*- coding: utf-8 -*-
from crysp.padding import *

import StringIO

# -----------------------------------------------------------------------------
# Mode of Operation Core class, default padding is nopadding.
class Mode(object):
    def __init__(self,cipher,pad=nopadding):
        self._cipher = cipher
        self.pad = pad(l=self.len)

    @property
    def len(self):
        return self._cipher.size/8

    def iterblocks(self,M,**kargs):
        nb,rb = divmod(len(M),self.len)
        P = StringIO.StringIO(M)
        for i in range(nb):
            yield P.read(self.len)
        yield self.pad.lastblock(P.read(rb),**kargs)

    # mandatory API:
    def enc(self,M):
        raise NotImplementedError
    def dec(self,C):
        raise NotImplementedError

    # xor input byte strings (over min length):
    def xorstr(self,a,b):
        return ''.join(map(lambda x,y: chr(x^y), map(ord,a),map(ord,b)))

# -----------------------------------------------------------------------------
# Electronic Code Book, default padding is pkcs7
class ECB(Mode):
    def __init__(self,cipher,pad=pkcs7):
        Mode.__init__(self,cipher,pad)
    # encryption mode
    def enc(self,M):
        C = []
        for b in self.iterblocks(M):
            C.append(self._cipher.enc(b))
        return ''.join(C)
    # decryption mode
    def dec(self,C):
        n,p = divmod(len(C),self.len)
        assert p==0
        P = StringIO.StringIO(C)
        M = []
        for b in range(n):
            M.append(self._cipher.dec(P.read(self.len)))
        return self.pad.remove(''.join(M))

# -----------------------------------------------------------------------------
# Cipher Block Chaining, default padding is pkcs7
class CBC(Mode):
    def __init__(self,cipher,IV,pad=pkcs7):
        Mode.__init__(self,cipher,pad)
        assert len(IV)==self.len
        self.IV = IV
    # encryption mode
    def enc(self,M):
        C = [self.IV]
        for b in self.iterblocks(M):
            x = self.xorstr(b,C[-1])
            C.append(self._cipher.enc(x))
        return ''.join(C)
    # decryption mode
    def dec(self,C):
        l = self.len
        n,p = divmod(len(C),l)
        assert p==0
        M = []
        while len(C)>l:
            c = C[-l:]
            C = C[:-l]
            M.insert(0,self.xorstr(C[-l:],self._cipher.dec(c)))
        return self.pad.remove(''.join(M))

# -----------------------------------------------------------------------------
# Counter mode with provided iterable counter (no padding)
class CTR(Mode):
    def __init__(self,cipher,counter=None):
        Mode.__init__(self,cipher)
        try:
            self.counter = (c for c in counter)
        except TypeError:
            print counter, 'is not iterable'

    # encryption mode
    def enc(self,M):
        self.__cache = []
        C = []
        for b in self.iterblocks(M):
            c = self.counter.next()
            self.__cache.append(c)
            k = self._cipher.enc(c)
            x = self.xorstr(b,k)
            C.append(x)
        return ''.join(C)
    # decryption mode
    def dec(self,C):
        n,p = divmod(len(C),self.len)
        assert p==0
        M = []
        P = StringIO.StringIO(C)
        for c in range(n):
            k = self._cipher.enc(self.__cache.pop(0))
            x = self.xorstr(P.read(self.len),k)
            M.append(x)
        return self.pad.remove(''.join(M))

# -----------------------------------------------------------------------------
# Chain mode of Operation Core class for Digest algorithms, nopadding default
class Chain(object):
    def __init__(self,cipherclass,pad=nopadding):
        self._cipherclass = cipherclass
        self.pad = pad

    def iterblocks(self,M,**kargs):
        nb,rb = divmod(len(M),self.len)
        P = StringIO.StringIO(M)
        for i in range(nb):
            yield P.read(self.len)
        yield self.pad.lastblock(P.read(rb),**kargs)

    # mandatory API:
    def __call__(self,M):
        raise NotImplementedError

    # xor input byte strings (over min length):
    def xorstr(self,a,b):
        return ''.join(map(lambda x,y: chr(x^y), map(ord,a),map(ord,b)))
