from git import Repo

repo = Repo(".")

diff = repo.git.diff()
print(diff)
