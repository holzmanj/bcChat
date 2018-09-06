initial_p_table = [
    [58, 50, 42, 34, 26, 18, 10, 2],
    [60, 52, 44, 36, 28, 20, 12, 4],
    [62, 54, 46, 38, 30, 22, 12, 6],
    [64, 56, 48, 40, 32, 24, 14, 8],
    [57, 49, 41, 33, 25, 17,  9, 1],
    [59, 51, 43, 35, 27, 19, 11, 3],
    [61, 53, 45, 37, 29, 21, 13, 5],
    [63, 55, 47, 39, 31, 23, 15, 7]
]

inverse_initial_p_table = [
    [40, 8, 48, 16, 56, 24, 64, 32],
    [39, 7, 47, 15, 55, 23, 63, 31],
    [38, 6, 46, 14, 54, 22, 62, 30],
    [37, 5, 45, 13, 53, 21, 61, 29],
    [36, 4, 44, 12, 52, 20, 60, 28],
    [35, 3, 43, 11, 51, 19, 59, 27],
    [34, 2, 42, 10, 50, 18, 58, 26],
    [33, 1, 41,  9, 49, 17, 57, 25]
]

def blockify(s, n):
    for x in range(0, len(s), n):
        yield s[x:x+n]
    
# converts string into list of bit strings
def str_to_bits(str):
    bytes = []
    for char in str:
        bytes.append(val_to_bitstr(ord(char), 8))
    return bytes

def bits_to_str(byte_list):
    str = ""
    for bitstr in byte_list:
        str += chr(int(bitstr, 2))
    return str

# converts number value to string of n bits
def val_to_bitstr(val, n):
    bits = bin(val)[2:]
    while(len(bits) < n):
        bits = '0' + bits
    return bits

# # converts string of bits back into numeric value
# def bitstr_to_val(bits):
#     val = 0
#     for i in range(len(bits)):
#         if bits[-(i+1)] == '1':
#             val += 2 ** i
#     return val

def permute_block(permutation_map, block):
    bit_rep = [[0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0]]
    
    new_rep = [[0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0]]

    ix = 0
    
    for c in block:
        bits = ("{0:b}".format(ord(c)))
        if len(bits) == 7:
            bits = '0' + bits
        for bit in bits:
            bit_rep[int(ix / 8)][ix % 8] = int(bit)
            ix += 1

    for r in range(8):
        for c in range(8):
            ix = permutation_map[r][c]
            new_rep[r][c] = bit_rep[int(ix / 8)][ix % 8]
            

    print(bit_rep)
    print(permutation_map)
    print(new_rep)
        
#def f(block, key):
    ## [expand block into 48 bits]
    #block += 
    
#def get_keylist(seed):
    ##[permutation table]

def encrypt(plaintext):
    while(len(plaintext) % 8 != 0):
        plaintext += ' '
    #plaintext = [ord(c) for c in plaintext]
    plaintext = str_to_bits(plaintext)
    
    for block in blockify(plaintext, 8):
        block = permute_block(initial_p_table, block)

        keys = get_keylist(input_key)
        
        l_block = block[:4]
        r_block = block[4:]

        for i in range(0, 16):
            tmp = r_block
            r_block = l_block ^ f(r_block, keys[i])
            l_block = tmp
        r_block, l_block = l_block, r_block

        ciphertext = permute_block()
        
