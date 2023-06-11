alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
alphabet_idx = {_c: _idx for _idx, _c in enumerate(alphabet)}


def bytes_to_52(b):
    base = len(alphabet)
    n = int.from_bytes(b, byteorder='big', signed=False)
    res = ""
    while n > 0:
        n, r = divmod(n, base)
        res = alphabet[r] + res
    return res


def s52_to_bytes(s):
    base = len(alphabet)
    n = 0
    for c in s:
        n = n * base + alphabet.index(c)
    b = n.to_bytes((n.bit_length() + 7) // 8, byteorder='big', signed=False)
    return b


def encode(string):
    flag = "0"
    process_str = string
    try:
        integer = int(string)
        process_str = "{:x}".format(integer)
        flag = "1"
    except ValueError:
        pass
    bs = (flag + process_str).encode("utf-8")
    reversed_bytes = bs[::-1]
    return bytes_to_52(reversed_bytes)


def decode(string):
    try:
        reversed_bytes = s52_to_bytes(string)
        bs_str = reversed_bytes[::-1].decode("utf-8")
        flag, process_str = bs_str[0], bs_str[1:]
        if flag == "0":
            return process_str
        if flag == "1":
            return str(int(f"0x{process_str}", 16))
        return None
    except:
        return None
