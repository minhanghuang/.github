import sys
import argparse
import json
import os
from collections import OrderedDict


class Parser:
    def __init__(self) -> None:
        self._parser = argparse.ArgumentParser()
        self._install_enable = None
        self._build_enable = None
        self._install_folder = ""
        self._build_folder = ""
        self._init_parser()

    def _init_parser(self):
        self._parser.add_argument(
            '--install_enable', type=bool, default=True, help='install enable')
        self._parser.add_argument(
            '--build_enable', type=bool, default=True, help='build enable')
        self._parser.add_argument(
            '--install_folder', type=str, default="third_party", help='install folder')
        self._parser.add_argument(
            '--build_folder', type=str, default="install", help='build folder')

    def start(self):
        params = vars(self._parser.parse_args())
        self._install_enable = params.get("install_enable")
        self._build_enable = params.get("build_enable")
        self._install_folder = params.get("install_folder")
        self._build_folder = params.get("build_folder")

    def get_install_enable(self):
        return self._install_enable

    def get_build_enable(self):
        return self._build_enable

    def get_install_folder(self):
        return self._install_folder

    def get_build_folder(self):
        return self._build_folder


class Repository:
    def __init__(self) -> None:
        self._addr = ""
        self._name = ""
        self._branch = ""
        self._before_script = ""
        self._options = ""

    def get_addr(self):
        return self._addr

    def get_name(self):
        return self._name

    def get_branch(self):
        return self._branch

    def get_before_script(self):
        return self._before_script

    def get_options(self):
        return self._options

    def set_addr(self, addr):
        self._addr = addr

    def set_name(self, name):
        self._name = name

    def set_branch(self, branch):
        self._branch = branch

    def set_before_script(self, before_script):
        self._before_script = before_script

    def set_options(self, options: list[str]):
        self._options = ""
        for option in options:
            self._options += " " + option


class Pipeline:
    def __init__(self) -> None:
        self._parser = Parser()
        self._repos = OrderedDict()
        self._current_path = os.path.abspath(__file__)
        self._download_path = ""
        self._install_path = ""
        self._packages_path = ""

    def init(self):
        self._load_params()
        self._loading_dependency()

    def check(self):
        if not os.path.exists(self._packages_path):
            print("packages.json文件不存在: {}".format(self._packages_path))
            exit(9)

    def download(self):
        for _, repo in self._repos.items():
            self._clone(repo=repo)

    def build(self):
        for name, repo in self._repos.items():
            os.chdir(os.path.join(self._download_path, name))
            cmd = "export LD_LIBRARY_PATH={0}/lib:$LD_LIBRARY_PATH && mkdir -p build && cd build && cmake .. -DCMAKE_INSTALL_PREFIX={0} {1}".format(
                self._install_path, repo.get_options())
            self._command(cmd=cmd)
            os.chdir("build")
            cmd = "make install -j4"
            self._command(cmd=cmd)

    def _clone(self, repo: Repository):
        cmd = ""
        download_path = os.path.join(self._download_path, repo.get_name())
        if os.path.exists(download_path):
            return
        self._command("mkdir -p {}".format(download_path))
        if "" == repo.get_branch():
            cmd = "git clone --depth 1 {} {}".format(
                repo.get_addr(),
                download_path)
        else:
            cmd = "git clone --depth 1 --single-branch --branch {} {} {}".format(
                repo.get_branch(),
                repo.get_addr(),
                download_path)
        self._command(cmd=cmd)

    def _command(self, cmd):
        print("cmd: {}".format(cmd))
        os.system(cmd)

    def _load_params(self):
        self._parser.start()
        self._download_path = os.path.join(
            os.path.dirname(self._current_path), str(self._parser.get_install_folder()))
        self._install_path = os.path.join(
            os.path.dirname(self._current_path), str(self._parser.get_build_folder()))
        self._packages_path = os.path.join(
            os.path.dirname(self._current_path), "packages.json")
        self._command("mkdir -p {}".format(self._download_path))
        self._command("mkdir -p {}".format(self._install_path))

    def _loading_dependency(self):
        with open(self._packages_path) as file:
            data = json.load(file, object_pairs_hook=OrderedDict)
        for name, repo in data["dependencies"].items():
            self._append_repository(
                addr=repo.get("addr"),
                branch=repo.get("commit", ""),
                before_script=repo.get("before_script", ""),
                options=repo.get("cmake_optione", "")
            )

    def _append_repository(self, **kwargs):
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
        self._repos[repo.get_name()] = repo


def main():
    pipe_line = Pipeline()
    pipe_line.init()
    pipe_line.check()
    pipe_line.download()
    pipe_line.build()


if __name__ == "__main__":
    main()
