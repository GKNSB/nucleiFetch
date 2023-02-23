import os
import shutil
import bisect
import hashlib
import subprocess


repos =    ["https://github.com/projectdiscovery/nuclei-templates.git",
			"https://github.com/0x727/ObserverWard_0x727",
			"https://github.com/1in9e/my-nuclei-templates",
			"https://github.com/5cr1pt/templates",
			"https://github.com/ARPSyndicate/kenzer-templates",
			"https://github.com/AshiqurEmon/nuclei_templates.git",
			"https://github.com/CharanRayudu/Custom-Nuclei-Templates",
			"https://github.com/clarkvoss/Nuclei-Templates",
			"https://github.com/d3sca/Nuclei_Templates",
			"https://github.com/daffainfo/my-nuclei-templates",
			"https://github.com/esetal/nuclei-bb-templates",
			"https://github.com/ethicalhackingplayground/erebus-templates",
			"https://github.com/geeknik/nuclei-templates-1",
			"https://github.com/geeknik/the-nuclei-templates",
			"https://github.com/Harish4948/Nuclei-Templates",
			"https://github.com/im403/nuclei-temp",
			"https://github.com/javaongsan/nuclei-templates",
			"https://github.com/kabilan1290/templates",
			"https://github.com/medbsq/ncl",
			"https://github.com/meme-lord/Custom-Nuclei-Templates",
			"https://github.com/MR-pentestGuy/nuclei-templates",
			"https://github.com/n1f2c3/mytemplates",
			"https://github.com/NitinYadav00/My-Nuclei-Templates",
			"https://github.com/notnotnotveg/nuclei-custom-templates",
			"https://github.com/obreinx/nuceli-templates",
			"https://github.com/optiv/mobile-nuclei-templates",
			"https://github.com/panch0r3d/nuclei-templates",
			"https://github.com/peanuth8r/Nuclei_Templates",
			"https://github.com/pikpikcu/my-nuclei-templates",
			"https://github.com/pikpikcu/nuclei-templates",
			"https://github.com/R-s0n/Custom_Vuln_Scan_Templates",
			"https://github.com/rafaelcaria/Nuclei-Templates",
			"https://github.com/rahulkadavil/nuclei-templates",
			"https://github.com/randomstr1ng/nuclei-sap-templates",
			"https://github.com/redteambrasil/nuclei-templates",
			"https://github.com/ree4pwn/my-nuclei-templates",
			"https://github.com/sadnansakin/my-nuclei-templates",
			"https://github.com/Saimonkabir/Nuclei-Templates",
			"https://github.com/Saptak9983/Nuclei-Template",
			"https://github.com/securitytest3r/nuclei_templates_work",
			"https://github.com/sharathkramadas/k8s-nuclei-templates",
			"https://github.com/shifa123/detections",
			"https://github.com/smaranchand/nuclei-templates",
			"https://github.com/Str1am/my-nuclei-templates",
			"https://github.com/System00-Security/backflow",
			"https://github.com/test502git/log4j-fuzz-head-poc",
			"https://github.com/thebrnwal/Content-Injection-Nuclei-Script",
			"https://github.com/thelabda/nuclei-templates",
			"https://github.com/yavolo/nuclei-templates",
			"https://github.com/z3bd/nuclei-templates",
			"https://github.com/zinminphyo0/KozinTemplates",
			"https://github.com/dwisiswant0/nuclei-templates.git"]


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


def main():
	initDirectories()
	cleanDirectories()
	counter = 0

	for repo in repos:
		counter += 1
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
