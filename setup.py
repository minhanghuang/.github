import sys
import os
from collections import OrderedDict

DEPENDENCES = [
    # "": [link, branch/tag, cmake options]
    ["https://github.com/minhanghuang/setup.git", "", ""],
    ["https://github.com/google/googletest.git", "", "-DCMAKE_CXX_STANDARD=14"],
    ["https://github.com/leethomason/tinyxml2.git", "", ""],
]


class Repository:
    def __init__(self) -> None:
        self.__link = ""
        self.__name = ""
        self.__branch = ""
        self.__options = ""

    def get_link(self):
        return self.__link

    def get_name(self):
        return self.__name

    def get_branch(self):
        return self.__branch

    def get_options(self):
        return self.__options

    def set_link(self, link):
        self.__link = link

    def set_name(self, name):
        self.__name = name

    def set_branch(self, branch):
        self.__branch = branch

    def set_options(self, options):
        self.__options = options


class Pipeline:
    def __init__(self) -> None:
        self.__repos = OrderedDict()
        self.__current_path = os.path.abspath(__file__)
        self.__download_path = os.path.join(
            os.path.dirname(self.__current_path), "third_party")
        self.__install_path = os.path.join(
            os.path.dirname(self.__current_path), "install")

    def init(self):
        os.system("mkdir -p {}".format(self.__download_path))
        os.system("mkdir -p {}".format(self.__install_path))

    def append_repository(self, **kwargs):
        repo = Repository()
        for key, value in kwargs.items():
            print(key, value)
            if "link" == key:
                repo.set_link(link=value)
                repo.set_name(name=value.rsplit(".", 1)[0].rsplit("/", 1)[-1])
            elif "branch" == key:
                repo.set_branch(branch=value)
            elif "options" == key:
                repo.set_options(options=value)
            else:
                print("Exception")
                exit(0)
        self.__repos[repo.get_name()] = repo

    def download(self):
        print("#######################")
        print("########### Download...")
        print("#######################")
        for _, repo in self.__repos.items():
            self.__clone(repo=repo)

    def build(self):
        print("#######################")
        print("############## Build...")
        print("#######################")
        for name, repo in self.__repos.items():
            os.chdir(os.path.join(self.__download_path, name))
            cmd = "mkdir -p build && cd build && cmake .. -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX={} {}".format(
                self.__install_path, repo.get_options())
            self.__cmd(cmd=cmd)
            os.chdir("build")
            cmd = "make install -j4"
            self.__cmd(cmd=cmd)

    def __clone(self, repo: Repository):
        cmd = ""
        download_path = os.path.join(self.__download_path, repo.get_name())
        if os.path.exists(download_path):
            return
        self.__cmd("mkdir -p {}".format(download_path))
        if "" == repo.get_branch():
            cmd = "git clone --depth 1 {} {}".format(
                repo.get_link(),
                download_path)
        else:
            cmd = "git clone --depth 1 --single-branch --branch {} {} {}".format(
                repo.get_branch(),
                repo.get_link(),
                download_path)
        self.__cmd(cmd=cmd)

    def __cmd(self, cmd):
        print("cmd: {}".format(cmd))
        os.system(cmd)


def main():
    pipe_line = Pipeline()
    pipe_line.init()
    for repo in DEPENDENCES:
        pipe_line.append_repository(
            link=repo[0], branch=repo[1], options=repo[2])
    pipe_line.download()
    pipe_line.build()


if __name__ == "__main__":
    main()
