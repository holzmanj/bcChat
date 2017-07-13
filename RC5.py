
class RC5:
    def __init__(self, W, R, key):
        self.W = W
        self.R = R
        self.key = key

    def _key_align(self):
        while len(self.key) % (self.W // 8):
            self.key += b'\x00'
        self.c = len(self.key) // (self.W // 8)
        L, key = [], bin(int.from_bytes(self.key, byteorder='little'))[2:]
        for i in range(self.c):
            L.append(int(key[:self.W], 2))


w = 32          # Length of a word in bits [Tweakable]
u = w/8         # Length of a word in bytes
b = 8           # Length of key in bytes [Tweakable]
K = [0]*b       # Key as array of bytes
c = int(b/u)    # Length of key in words
L = [0]*c       # Temp working array for key scheduling
r = 12          # Number of rounds [Tweakable]
t = 2*(r+1)     # Number of round subkeys required
S = [0]*t       # Round subkey words
P = 0xB7E15163  # First magic constant (dependent on w)
Q = 0x9E3779B9  # Second magic constant (dependent on w)


def setup():
    L[c-1] = 0
    for i in range(b-1, -1, -1):
        L[i/u] = (L[int(i/u)] << 8) + K[i]

    S[0] = P
    for i in range(1, t):
        S[i] = S[i-1] + Q