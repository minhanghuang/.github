import sys
import json
import os
from collections import OrderedDict


class Repository:
    def __init__(self) -> None:
        self.__addr = ""
        self.__name = ""
        self.__branch = ""
        self.__before_script = ""
        self.__options = ""

    def get_addr(self):
        return self.__addr

    def get_name(self):
        return self.__name

    def get_branch(self):
        return self.__branch

    def get_before_script(self):
        return self.__before_script

    def get_options(self):
        return self.__options

    def set_addr(self, addr):
        self.__addr = addr

    def set_name(self, name):
        self.__name = name

    def set_branch(self, branch):
        self.__branch = branch

    def set_before_script(self, before_script):
        self.__before_script = before_script

    def set_options(self, options: list[str]):
        self.__options = ""
        for option in options:
            self.__options += " " + option


class Pipeline:
    def __init__(self) -> None:
        self.__repos = OrderedDict()
        self.__current_path = os.path.abspath(__file__)
        self.__download_path = os.path.join(
            os.path.dirname(self.__current_path), "third_party")
        self.__install_path = os.path.join(
            os.path.dirname(self.__current_path), "install")
        self.__packages_path = os.path.join(
            os.path.dirname(self.__current_path), "packages.json")

    def check(self):
        if not os.path.exists(self.__packages_path):
            print("packages.json文件不存在: {}".format(self.__packages_path))
            exit(9)

    def init(self):
        os.system("mkdir -p {}".format(self.__download_path))
        os.system("mkdir -p {}".format(self.__install_path))
        self.__loading()

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
            cmd = "export LD_LIBRARY_PATH={0}/lib:$LD_LIBRARY_PATH && mkdir -p build && cd build && cmake .. -DCMAKE_INSTALL_PREFIX={0} {1}".format(
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
                repo.get_addr(),
                download_path)
        else:
            cmd = "git clone --depth 1 --single-branch --branch {} {} {}".format(
                repo.get_branch(),
                repo.get_addr(),
                download_path)
        self.__cmd(cmd=cmd)

    def __cmd(self, cmd):
        print("cmd: {}".format(cmd))
        os.system(cmd)

    def __append_repository(self, **kwargs):
        repo = Repository()
        for key, value in kwargs.items():
            if "addr" == key:
                repo.set_addr(addr=value)
                repo.set_name(name=value.rsplit(".", 1)[0].rsplit("/", 1)[-1])
            elif "branch" == key:
                repo.set_branch(branch=value)
            elif "before_script" == key:
                repo.set_before_script(before_script=value)
            elif "options" == key:
                repo.set_options(options=value)
            else:
                print("Exception")
                exit(0)
        self.__repos[repo.get_name()] = repo

    def __loading(self):
        with open(self.__packages_path) as file:
            data = json.load(file, object_pairs_hook=OrderedDict)
        for name, repo in data["dependencies"].items():
            self.__append_repository(
                addr=repo.get("addr"),
                branch=repo.get("commit", ""),
                before_script=repo.get("before_script", ""),
                options=repo.get("cmake_optione", "")
            )


def main():
    pipe_line = Pipeline()
    pipe_line.check()
    pipe_line.init()
    pipe_line.download()
    pipe_line.build()


if __name__ == "__main__":
    main()
