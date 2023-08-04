import sys
import argparse
import json
import os
from collections import OrderedDict

__SETUP_VERSION__ = "1.1.0"


class Template:
    def __init__(self) -> None:
        self._current_path = os.path.abspath(os.path.dirname(__file__))
        self._download_path = ""
        self._install_path = ""

    def set_download_path(self, path):
        self._download_path = path

    def set_install_path(self, path):
        self._install_path = path

    def get_template(self):
        return {
            "current_path": self._current_path,
            "download_path": self._download_path,
            "install_path": self._install_path
        }


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


class Script:
    def __init__(self) -> None:
        self._before = []
        self._after = []

    def set_before(self, script: list):
        self._before = script

    def set_after(self, script: list):
        self._after = script

    def get_before(self):
        return self._before

    def get_after(self):
        return self._after


class Repository:
    def __init__(self) -> None:
        self._addr = ""
        self._name = ""
        self._branch = ""
        self._before_script = ""
        self._options = ""
        self._install_path = ""

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

    def get_install_path(self):
        return self._install_path

    def set_addr(self, addr):
        self._addr = addr

    def set_name(self, name):
        self._name = name

    def set_branch(self, branch):
        self._branch = branch

    def set_before_script(self, before_script):
        self._before_script = before_script

    def set_options(self, options):
        self._options = options

    def is_git_repository(self) -> bool:
        return self._addr.endswith(".git")

    def set_install_path(self, install_path):
        self._install_path = install_path


class Pipeline:
    def __init__(self) -> None:
        self._parser = Parser()
        self._repos = OrderedDict()
        self._scripts = Script()
        self._template = Template()
        self._current_path = os.path.abspath(os.path.dirname(__file__))
        self._download_path = ""
        self._install_path = ""
        self._packages_path = ""
        self._pkg_config_path = ""

    def init(self):
        self._load_params()
        self._loading_packages()
        self._before_script()

    def download(self):
        for _, repo in self._repos.items():
            self._clone_git_repository(repo=repo)
            self._download_compress_files(repo=repo)

    def build(self):
        for name, repo in self._repos.items():
            if not repo.is_git_repository():
                continue
            repo_path = os.path.join(self._download_path, name)
            os.chdir(repo_path)
            cmd = "export PKG_CONFIG_PATH={0}/lib/pkgconfig:{0}/shared/pkgconfig:{1} && mkdir -p build && cd build && cmake .. {2}".format(
                self._install_path, self._pkg_config_path, repo.get_options())
            self._command(cmd=cmd)
            os.chdir("build")
            cmd = "make install -j4"
            self._command(cmd=cmd)

    def exit(self):
        self._after_script()

    def _clone_git_repository(self, repo: Repository):
        cmd = ""
        download_path = os.path.join(self._download_path, repo.get_name())
        if os.path.exists(download_path):
            return
        if not repo.is_git_repository():
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

    def _download_compress_files(self, repo: Repository):
        cmd = ""
        download_path = os.path.join(self._download_path, repo.get_name())
        if os.path.exists(download_path) or not repo.get_addr():
            return
        if repo.is_git_repository():
            return

        print("#### download compress file: {}".format(repo.get_addr()))
        # remove packages file
        for file_name in os.listdir(self._download_path):
            file_path = os.path.join(self._download_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # download
        cmd = "wget -P {} {}".format(self._download_path, repo.get_addr())
        self._command(cmd=cmd)

        # unpack
        temp_path = os.path.join(self._download_path, ".zip_temp")
        os.makedirs(temp_path)
        for file_name in os.listdir(self._download_path):
            file_path = os.path.join(self._download_path, file_name)
            if os.path.isfile(file_path):
                cmd = ""
                if file_name.endswith(".zip"):
                    cmd = "unzip -d {} {}".format(
                        temp_path, file_path)
                elif file_name.endswith(".tar.gz"):
                    cmd = "tar -C {} -zxvf {}".format(
                        self._download_path, file_path)
                elif file_name.endswith(".tar"):
                    cmd = "tar -C {} -xvf {}".format(
                        self._download_path, file_path)
                self._command(cmd=cmd)
                break

        # move
        for file_name in os.listdir(temp_path):
            file_path = os.path.join(temp_path, file_name)
            if os.path.isdir(file_path) and repo.get_install_path():
                # 修改文件夹名
                cmd = "mv {} {}".format(
                    file_path, os.path.join(temp_path, repo.get_name()))
                self._command(cmd=cmd)
                # 移动
                cmd = "mv {} {}".format(os.path.join(temp_path, repo.get_name()), os.path.join(
                    self._current_path, repo.get_install_path()))
                self._command(cmd=cmd)
                break

    def _command(self, cmd):
        if "" != cmd:
            print("cmd: {}".format(cmd))
            os.system(cmd)

    def _load_params(self):
        self._parser.start()
        self._download_path = os.path.join(
            self._current_path, str(self._parser.get_install_folder()))
        self._install_path = os.path.join(
            self._current_path, str(self._parser.get_build_folder()))
        self._packages_path = os.path.join(self._current_path, "packages.json")
        if not os.path.exists(self._packages_path):
            print("packages.json文件不存在: {}".format(self._packages_path))
            sys.exit(9)
        self._command("mkdir -p {}".format(self._download_path))
        self._command("mkdir -p {}".format(self._install_path))
        self._template.set_download_path(self._download_path)
        self._template.set_install_path(self._install_path)

        if os.getenv("PKG_CONFIG_PATH"):
            self._pkg_config_path = "{}".format(os.getenv("PKG_CONFIG_PATH"))
        else:
            self._pkg_config_path = ""

    def _loading_packages(self):
        with open(self._packages_path) as file:
            data = json.load(file, object_pairs_hook=OrderedDict)
        for name, repo in data["dependencies"].items():
            self._append_repository(
                name=name,
                addr=self._parse_addr(repo.get("addr")),
                branch=repo.get("commit", ""),
                before_script=repo.get("before_script", ""),
                install_path=repo.get("install_path", ""),
                options=repo.get("cmake_optione", "")
            )
        self._scripts.set_before(data["scripts"].get("before", []))
        self._scripts.set_after(data["scripts"].get("after", []))

    def _before_script(self):
        for script in self._scripts.get_before():
            self._command(script.format(**self._template.get_template()))

    def _after_script(self):
        for script in self._scripts.get_after():
            self._command(script)

    def _append_repository(self, **kwargs):
        repo = Repository()
        for key, value in kwargs.items():
            if "addr" == key:
                repo.set_addr(addr=value)
            elif "name" == key:
                repo.set_name(name=value)
            elif "install_path" == key:
                repo.set_install_path(install_path=value)
            elif "branch" == key:
                repo.set_branch(branch=value)
            elif "before_script" == key:
                repo.set_before_script(before_script=value)
            elif "options" == key:
                options = ""
                for option in value:
                    options += " " + \
                        option.format(**self._template.get_template())
                repo.set_options(options=options)
            else:
                print("Exception")
                exit(0)
        self._repos[repo.get_name()] = repo

    def _parse_addr(self, addr) -> str:
        if isinstance(addr, str):
            return addr
        elif isinstance(addr, dict):
            return ""
        else:
            print("packages.json addr Exception")
            sys.exit(9)


def main():
    print("setup version: {}".format(__SETUP_VERSION__))
    pipe_line = Pipeline()
    pipe_line.init()
    pipe_line.download()
    pipe_line.build()
    pipe_line.exit()


if __name__ == "__main__":
    main()
