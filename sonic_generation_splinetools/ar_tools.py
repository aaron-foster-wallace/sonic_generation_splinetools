import os
import io
import struct
import re
import functools
import itertools
import tempfile

"""
Return a tuple (header,file_dictionary),
Where header is the file original header #for recreate the file exactly if is needed
And file_dictionary is a dictionary
keys are filename and values ftuple=(position,flen,(seglen,flen,hlen,unk1,unk2))
(seglen,flen,hlen,unk1,unk2) is also #for recreate the file exactly if is needed
"""
ARHEADER=(0,16,20)

def getARFileInfo(ar_filename):
    f = open(ar_filename, "rb")
    filetuples={}    
    f = open(ar_filename, "rb")
    headbf=f.read(16)
    # no validate  most be (w1,w2,w3) ==ARHEADER
    (w1,w2,w3,padding)=struct.unpack_from("<LLLL",headbf)
    if (w1,w2,w3) !=ARHEADER:
        print("Warning WRONG AR FILE HEADER")
    while True:
        hpos=f.tell()
        fheaderbuf=f.read(20)
        if len(fheaderbuf)<20: break
        (seglen,flen,hlen,unk1,unk2)=struct.unpack_from("<LLLLL",fheaderbuf)
        filename=''.join(iter(lambda: f.read(1).decode('ascii'), '\x00'))
        #f.seek(hpos+hlen,0)
        #filebf=f.read(flen)
        filetuples[filename]=(hpos+hlen,flen,(seglen,flen,hlen,unk1,unk2))
        f.seek(hpos+seglen,0)
    f.close()
    return (padding,filetuples)

def getFileBuffer(f,filetuple):
    (position,flen,_)=filetuple
    f.seek(position,0)
    return f.read(flen)

def extractArFiles(ar_filename,directory):
    (padding,filetuples)=getARFileInfo(ar_filename)    
    f = open(ar_filename, "rb")    
    for fname,filetuple in filetuples.items():
        getFileBuffer(f,filetuple)
        (_,flen,_)=filetuple
        nf=open(os.path.join(directory,fname),"wb")
        nf.write(getFileBuffer(f,filetuple))
        nf.close()
    f.close()



def extractArFileToTempDir(ar_filename):
    print(ar_filename)
    basedir=os.path.dirname(ar_filename)
    tmp_dirpath = tempfile.mkdtemp(prefix="extracted-"+os.path.basename(ar_filename),dir=basedir)
    extractArFiles(ar_filename,tmp_dirpath)
    return tmp_dirpath
       


def joinArFiles(file_list,ar_filename,padding=64):
    arf = open(ar_filename, "wb")    
    arf.write(struct.pack("<LLLL",*ARHEADER,padding))    
    for sf in file_list:
        #Write file to Ar
        sfb=os.path.basename(sf)
        hlen = 20 + len(sfb) + 1
        off = (hlen + arf.tell()) % padding
        if off != 0:
            hlen += padding - off        
        #Here must be the #Multiple file soupport check c#     
        fheadpos=arf.tell()
        arf.seek(8,1)#skip segment & header len 
        arf.write(struct.pack("<LLL",hlen,0,0))
        arf.write(bytes(sfb,"ascii"))
        #arf.write("\0")
        off =arf.tell() % padding
        spad=b"\0"*(padding-off)
        if spad:
            arf.write(spad)
        f=open(sf,"rb")
        arf.write(f.read())

        #Write FileInfo Header
        fsize=f.tell()
        f.close()
        resumeat=arf.tell()        
        arf.seek(fheadpos)
        arf.write(struct.pack("<LL",hlen+fsize,fsize))
        arf.seek(resumeat)
    arf.close()


def joinARFilesFromDir(directory,arfilename):
    files=os.listdir(directory)
    files=[os.path.join(directory,f) for f in files]
    files=[f for f in files if os.path.isfile(f)]
    joinArFiles(files,arfilename)





"""


Technical stuff: AR format

 /!\ IMPORTANT/!\
The AR format is Little endian


Each AR file begins with 4 32 bit integers. In most cases they are:

0x00000000: 00000000
0x00000004: 00000010 
0x00000008: 00000014 
0x0000000C: 00000040

In rare cases they change.. I do not really know what they do! They are stored
to !archive-info.xml during extraction. The a file segment begins:

[File segments]
File segments begin on any given address in an AR file.. they are not aligned!
They start with a little file header containing the following information (in
exactly that order - base address is the begin of a file segment):

Header:
0x00000000: Length of the complete file segment
0x00000004: Length of the file to unpack
0x00000008: Length of the header
0x0000000C: Unknown1 (stored to !archive-info.xml - shouldn't be changed)   
0x00000010: Unknown2 (stored to !archive-info.xml - shouldn't be changed)
0x00000014: File name as ASCII string null-terminated
After filename: a bunch of zeros - until the actual file starts - it fills each
header with 0s until the address in the AR file is a multiple of 0x00000040 .

File content:
uncompressed file data - length given in the header (position 0x00000004)
"""






