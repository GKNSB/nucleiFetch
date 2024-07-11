import os
import shutil
import bisect
import hashlib
import requests
import subprocess
from hashlib import md5
import Levenshtein


MAX_FILE_SIZE = 100 * 1024  # 100 KB


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
		filename = item
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


def read_file_as_binary(file_path):
	try:
		with open(file_path, 'rb') as file:
			return file.read()
	except Exception as e:
		print(f"Error reading file {file_path}: {e}")
		return b""


def remove_id_info_sections(file_content):
    lines = file_content.splitlines()
    new_lines = []
    skip_info = False

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(b'id:'):
            continue
        elif stripped_line.startswith(b'info:'):
            skip_info = True
            continue
        elif skip_info:
            if not line.startswith(b' ') and not stripped_line == (b''):
                skip_info = False
        if not skip_info:
            new_lines.append(line)
    
    return b"\n".join(new_lines)


def hash_content(content):
	return md5(content).hexdigest()


def second_deduplication(file_paths):
	seen_hashes = set()
	deduped_files = set()
	
	for file in file_paths:
		try:
			file_content = read_file_as_binary(file)
			if file_content == b"":
				continue
			
			content_without_id_info = remove_id_info_sections(file_content)
			content_hash = hash_content(content_without_id_info)

			if content_hash not in seen_hashes:
				seen_hashes.add(content_hash)
				deduped_files.add(file)

		except Exception as e:
			print(f"Error processing file {file}: {e}")
		
	return deduped_files


def read_file_as_binary2(file_path):
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            return None
        with open(file_path, 'rb') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return b""


def are_files_similar(content1, content2, threshold=2):
    content1_str = content1.decode('utf-8', errors='ignore')
    content2_str = content2.decode('utf-8', errors='ignore')

    distance = Levenshtein.distance(content1_str, content2_str)

    return distance <= threshold


def third_deduplication(file_paths, similarity_threshold=2, max_recent_files=1000):
    recent_files = []
    copied = 0
    non_similar = set()

    sorted_file_paths = sorted(file_paths, key=lambda x: os.path.basename(x))

    for i, file in enumerate(sorted_file_paths):
        try:
            file_content = read_file_as_binary2(file)
            if file_content is None:
                non_similar.add(file)
                copied += 1
                recent_files.append(file)
                if len(recent_files) > max_recent_files:
                    recent_files.pop(0)
                continue
            if file_content == b"":
                continue

            content_without_id_info = remove_id_info_sections(file_content)

            is_unique = True
            for recent_file in recent_files:
                recent_file_content = read_file_as_binary2(recent_file)
                if recent_file_content is None:
                    continue
                recent_content = remove_id_info_sections(recent_file_content)
                if are_files_similar(content_without_id_info, recent_content, similarity_threshold):
                    is_unique = False
                    break

            if is_unique:
                recent_files.append(file)
                if len(recent_files) > max_recent_files:
                    recent_files.pop(0)
                non_similar.add(file)
                copied += 1
        except Exception as e:
            print(f"Error processing file {file}: {e}")

    return non_similar


def first_deduplication(tempDirContents):
	sortedNames = []
	sortedFilepath = []
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
			sortedNames.append(filename)
			sortedNames.sort()
			sortedFilepath.append(fileAndHash['file'])
			sortedFilepath.sort()
			sortedHashes.append(filehash)
			sortedHashes.sort()

	return sortedFilepath


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
	print(f"[*] Deduping downloaded files {len(tempDirContents)}...")

	print(f" > First deduplication based on filehash or filename...")
	first_deduped_files = first_deduplication(tempDirContents)
	print(f" > Resulting files: {len(first_deduped_files)}")

	print(f" > Second deduplication based on hash of template code (without id and info)...")
	second_deduped_files = second_deduplication(first_deduped_files)
	print(f" > Resulting files: {len(second_deduped_files)}")

	print(f" > Third deduplication based on levenshtein distance of templates...")
	third_deduped_files = third_deduplication(second_deduped_files)
	print(f" > Resulting files: {len(third_deduped_files)}")

	populateDirectories(third_deduped_files)

	print(f"[*] Total templates: {len(tempDirContents)}")
	print(f"[*] Unique templates: {len(os.listdir('./templates-latest/'))}")
	print(f"[*] New templates: {len(os.listdir('./templates-onlynew/'))}")


if __name__ == "__main__":
	main()
