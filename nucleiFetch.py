import os
import shutil
import bisect
import hashlib
import requests
import subprocess


def getMD5(file):
	return hashlib.md5(open(file, "rb").read()).hexdigest()


def makeDirDict(directory):
	command = f"find {directory} -type f -name \"*.yaml\""
	pm = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	out, err = pm.communicate()
	mylist = out.decode("utf-8").split("\n")

	yamls = ([x for x in mylist if x])

	filesAndHashes = []
	for yaml in yamls:
		filesAndHashes.append({"file":yaml, "filehash":getMD5(yaml)})

	return filesAndHashes


def initDirectories():
	os.makedirs("./tmp/", exist_ok=True)
	os.makedirs("./templates-previous/", exist_ok=True)
	os.makedirs("./templates-onlynew/", exist_ok=True)
	os.makedirs("./templates-latest/", exist_ok=True)


def cleanDirectories():
	folders = os.listdir("./tmp/")
	for folder in folders:
		shutil.rmtree(f"./tmp/{folder}")

	files = os.listdir("./templates-previous/")
	for file in files:
		os.remove(f"./templates-previous/{file}")

	files = os.listdir("./templates-onlynew/")
	for file in files:
		os.remove(f"./templates-onlynew/{file}")

	files = os.listdir("./templates-latest/")
	for file in files:
		shutil.copy(f"./templates-latest/{file}", "./templates-previous")

	files = os.listdir("./templates-latest/")
	for file in files:
		os.remove(f"./templates-latest/{file}")


def populateDirectories(items):
	for item in items:
		filename = item["file"]
		shutil.copy(filename, "./templates-latest/")

		if filename.split("/")[-1] not in os.listdir("./templates-previous"):
			shutil.copy(filename, "./templates-onlynew/")


def inSortedList(elem, sorted_list):
	i = bisect.bisect_left(sorted_list, elem)
	return i != len(sorted_list) and sorted_list[i] == elem


def readRepos():
	lines = []
	with open("./repos.txt") as infile:
		for line in infile:
			lines.append(line.strip())
	return lines


def checkRepo(repo):
	headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
	resp = requests.get(repo, headers=headers)
	if resp.status_code == 404:
		return False
	else:
		return True


def main():
	initDirectories()
	cleanDirectories()
	counter = 0
	repos = readRepos()

	for repo in repos:
		counter += 1
		
		if checkRepo(repo):
			command = f"git clone {repo} ./tmp/repo{counter}"
			print(f"[*] Cloning {repo} into ./tmp/repo{counter}")
			p = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
			p.wait()

			os.mkdir(f"./tmp/repo{counter}/arandomdirname/")
			os.chdir(f"./tmp/repo{counter}")

			command = f"for item in `git for-each-ref refs/remotes/origin --format='%(refname)' | grep -v 'HEAD$'`; do echo -n ./arandomdirname/`echo $item | rev | cut -d\"/\" -f1 | rev`; echo -n \" \"; echo $item; done | xargs -n 2 git worktree add"
			p = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
			p.wait()

			os.chdir(f"../../")
		else:
			print(f"[-] Broken repo: {repo}")

	tempDirContents = makeDirDict("./tmp")
	outDirContents = []
	print(f"[*] Deduping downloaded files...")

	sortedNames = []
	sortedHashes = []

	for fileAndHash in tempDirContents:
		filename = fileAndHash['file'].split("/")[-1]
		filehash = fileAndHash['filehash']

		found = False

		if inSortedList(filehash, sortedHashes) and inSortedList(filename, sortedNames):
			found = True

		elif inSortedList(filehash, sortedHashes) and not inSortedList(filename, sortedNames):
			found = True

		elif inSortedList(filename, sortedNames) and not inSortedList(filehash, sortedHashes):
			found = True

		else:
			outDirContents.append(fileAndHash)
			sortedNames.append(filename)
			sortedNames.sort()
			sortedHashes.append(filehash)
			sortedHashes.sort()

	populateDirectories(outDirContents)

	print(f"[*] Total templates: {len(tempDirContents)}")
	print(f"[*] Unique templates: {len(os.listdir('./templates-latest/'))}")
	print(f"[*] New templates: {len(os.listdir('./templates-onlynew/'))}")


if __name__ == "__main__":
	main()
