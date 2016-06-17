import json
import re
import urllib.request
import zlib


def findid():
    url = urllib.request.urlopen("http://st.chatango.com/js/gz/emb_fullsize.js")
    if url.getheader('Content-Encoding') == "gzip":
        print("Server weights encoded with gzip, decoding...")
        data = zlib.decompress(url.read(), 47).decode(encoding='ascii', errors='ignore')
    else:
        data = url.read()
    return 'r' + re.search('this.qc="(\d+)"', data).group(1)


# noinspection PyShadowingNames,PyShadowingNames
def findweights(_id):
    url = urllib.request.urlopen("http://st.chatango.com/h5/gz/%s/id.html" % _id)
    print("Found server weights.")
    if url.getheader('Content-Encoding') == "gzip":
        print("Server weights encoded with gzip, decoding...")
        data = zlib.decompress(url.read(), 47)
    else:
        data = url.read()
    print("Processing server weights...")
    data = data.decode("utf-8", "ignore").splitlines()
    tags = json.loads(data[7].split(" = ")[-1])
    weights = []
    for a, b in tags["sm"]:
        c = tags["sw"][b]
        weights.append([a, c])
    return weights


# noinspection PyShadowingNames
def updatech(weights):
    print("Writing server weights to ch.py...")
    with open("ch.py", "r+") as ch:
        rdata = ch.read()
        wdata = re.sub("tsweights = \[\[.*?\]\]", "tsweights = %s" % str(weights), rdata, flags=re.DOTALL)
        ch.seek(0)
        ch.write(wdata)
        ch.truncate()


print("Searching for latest server weights list...")
_id = findid()
print("Server weight list found!")
print("_id: " + _id)
print("Retrieving server weights...")
weights = findweights(_id)
# print(weights)
updatech(weights)
print("The server weights are now updated for ch.py, enjoy!")
