def exists(v):
    return v in vars() or v in globals()

x = 1
print(exists('x'))
print(exists('y'))