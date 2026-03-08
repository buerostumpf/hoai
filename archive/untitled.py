myvar = 25 + 3
yourvar = myvar/2
print ("Hello World: ", myvar)
print ("Hello New World",myvar,int(yourvar),sep=" - ")
print ("In binary this means: ",bin(myvar) ,bin(int(yourvar)) ,sep=", ")

for i in range(4):
    if (i == 2):
        print ("Bla")
    else:
        print (i)
    
print (id(myvar),id(yourvar), sep=", ")
