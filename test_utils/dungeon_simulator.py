class A:
    def use(self):
        del self


values = [A(), A()]
print(values)
values[0].use()
print(values)
values[0].use()
print(values)
