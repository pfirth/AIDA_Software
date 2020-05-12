





a = 1235
b = 2000

c = 100*(a/b)

command = "S1{:.1f}"

final_commanbd = command.format(c)
final_commanbd = str.encode(final_commanbd,"utf-8")

print(final_commanbd)

