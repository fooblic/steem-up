#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''Encrypt / decrypt a file'''
import pyelliptic
import getpass
import base64
import os, sys


def encr(myfile):

    if os.path.isfile(myfile):
        print("File %s already exist. Are u sure to rewrite it (y/n)?" % myfile)
        cmd = input("encrypt>")
        if cmd != "y":
            print("Exit")
            return

    print("Encrypt..")
    key = getpass.getpass()
    print("And again..")
    key2 = getpass.getpass()
    if (key != key2):
        print("2 passwords are different, try again...")
        return

    out = ""
    for line in open(myfile, "r"):
        out += line

    iv = pyelliptic.Cipher.gen_IV('bf-cfb')
    bi = base64.encodestring(iv)
    ctx = pyelliptic.Cipher(key, iv, 1, ciphername='bf-cfb')
    del key

    ciphertext = ctx.update(out)
    del out
    ciphertext += ctx.final()
    ctext = base64.encodestring(ciphertext)

    with open(myfile, "w") as f:
        f.write(str(bi, "utf8"))     #;print(bi)
        f.write(str(ctext, "utf8"))  #;print(ctext)

    print("Done.")


def show_decr(myfile):
    '''decryption'''

    ctext = ""
    with open(myfile, "r") as f:
        iv = base64.b64decode(f.readline().strip())
        for line in f:
            ctext += line

    print("Dencrypt..")
    key = getpass.getpass()

    ctx2 = pyelliptic.Cipher(key, iv, 0, ciphername='bf-cfb')
    del key

    try:
        out = str(ctx2.ciphering(base64.b64decode(ctext)), 'utf8')  # not cyrillic?
    except:
        return("Error")

    return out


def save_decr(myfile):
    out = show_decr(myfile)
    if out != "Error":
        print("File %s already exist. Are u sure to rewrite it (y/n)?" % myfile)
        cmd = input("save>")
        if cmd != "y":
            print("Exit")
            return
        else:
            with open(myfile, "w") as f:
                f.write(out)  ;print(out)

            print("ok")
    else:
        print("Error")
    return


def check_file(myfile):
    while not os.path.isfile(myfile):
        print("File %s not exist..." % myfile)
        myfile = input("Enter local file name: ")

    return myfile

### Main

myfile = ""

if len(sys.argv) == 2:
    myfile = "./" + sys.argv[1]
    myfile = check_file(myfile)
else:
    myfile = check_file(myfile)

cmd = ""
hlp = '''Enter:
        e - encrypt
        d - decrypt
        s - save decryped
        f - print file name
        c - change file name
        h - help
        q - quit
        '''

while cmd != "q":
    cmd = input("cmd>")
    if cmd == "e":
        encr(myfile)
    elif cmd == "d":
        print(show_decr(myfile))
    elif cmd == "s":
        save_decr(myfile)
    elif cmd == "f":
        print("File name: %s" % myfile)
    elif cmd == "c":
        myfile = ""
        myfile = check_file(myfile)
    elif cmd == "h":
        print(hlp)
    elif cmd == "":
        print("Enter h - for help")
    elif cmd == "q":
        print("Bye!")
        sys.exit(0)   

