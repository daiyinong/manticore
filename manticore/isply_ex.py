import islpy as isl

domain = isl.Set("{[x, y] : -2147483648 <= x <= 2147483647 and 0 <= y <= 2147483647 }")
set = isl.Set("{[x, y] : x > 10 and y <= x }")
set = set.intersect(domain)

print("set : %s" % set)
print(set.card())

