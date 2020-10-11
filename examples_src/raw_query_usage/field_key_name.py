from odmantic import Field, Model


class User(Model):
    name: str = Field(key_name="username")


print(+User.name)
#> username

print(++User.name)
#> $username
