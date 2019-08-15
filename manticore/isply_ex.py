import islpy as isl

space = isl.Space.create_from_names(isl.DEFAULT_CONTEXT, set=["x", "y"])

domain = isl.Set("{[x, y] : -2147483648 <= x <= 2147483647 and 0 <= y <= 2147483647 }")

bset2 = isl.Set("{[x, y] : x != 1000 }")

bset2 = bset2.intersect(domain)

print("set 2: %s" % bset2)
print(bset2.card())

