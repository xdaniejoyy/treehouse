from scipy.special import comb


def pascal_triangle(N):
    try:
        N = int(N)
    except:
        raise ValueError("N must be an integer.")

    if N <= 0:
        raise ValueError("N must be an int > 0.")

    unique_values = (N - 1) // 2
    vals = []
    for k in range(unique_values + 1):
        vals.append(comb(N-1, k))

    if N % 2: # odd number, don't repeat last value
        return vals + vals[-2::-1]
    # even number, symmetrical list
    return vals + vals[::-1]

n = 10
print(f"n={n}: ", pascal_triangle(n))
