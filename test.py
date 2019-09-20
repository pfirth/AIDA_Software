

a = {22:'a',25:'b'}

l = [21,22,23,24,25]

for n in l:
    try:
        print(a[n])

    except KeyError:
        a[n] = 'new'
        print(a[n])

