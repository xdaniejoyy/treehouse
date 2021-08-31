import os
import re
import shutil
import subprocess
import time
from pathlib import Path


class RepoStats():

    """
    Clone repo, get repo statistics, delete repo.
    cloc returns statistics of the repository in the following format:
     '---------------------------------------------------------------',
     'Language                 files      blank    comment       code',
     '---------------------------------------------------------------',
     'Python                     123       1000       2000       3000',
    """

    def _clone_repo(self):
        """
        Clone repository.
        :return:
        """
        subprocess.Popen(['git', 'clone', self.repo, 'target_repo'],
                         stdout=subprocess.PIPE)
        # Give some time before continuing
        time.sleep(5)

    @staticmethod
    def delete_repo():
        """
        Delete repository.
        :return:
        """
        shutil.rmtree('target_repo', ignore_errors=True)


    def __init__(self, repo):
        self.repo = repo

        self._clone_repo()

    @staticmethod
    def get_file_count(language='Python'):
        """
        Get file count of a language, default 'Python'
        :return: int, number of files
        """
        assert language is not None

        # Get stats from cloc
        result = subprocess.Popen('cloc target_repo',
                                  stdout=subprocess.PIPE,
                                  shell=True)
        result_formatted = str(result.communicate()).split('\\n')

        # Count Python files, lines of code
        files = 0
        for line in result_formatted:
            if line[:len(language)] == language:
                files = int([x.strip() for x in line.split()][1])
                break
        return files

    @staticmethod
    def get_lines_count(language='Python'):
        """
        Get lines (total, commented) count of a language, default 'Python'
        :return: list, number of lines (total, commented)
        """
        assert language is not None

        # Get stats from cloc
        result = subprocess.Popen('cloc target_repo',
                                  stdout=subprocess.PIPE,
                                  shell=True)
        result_formatted = str(result.communicate()).split('\\n')

        # Count files, lines of code
        code, comment = 0, 0
        for line in result_formatted:
            if line[:len(language)] == language:
                comment, code = [x.strip() for x in line.split()][-2:]
                break
        return [int(code), int(comment)]

    @staticmethod
    def get_function_count(language='Python'):
        """
        Count functions, by using grep for "def " in any .py file
        :return: int, number of functions
        """
        if language != 'Python':
            raise ValueError("Language not implemented.")

        result_fn = subprocess.Popen('cd target_repo && git grep -c "def "',
                                     stdout=subprocess.PIPE, shell=True)
        functions = str(result_fn.communicate()[0]).split('\\n')
        function_count = 0
        for line in functions:
            try:
                file, count = line.split(":")
                if file[-3:] == '.py':
                    function_count += int(count)
            except:
                continue
        return function_count

    @staticmethod
    def get_linechange_count():
        """
        Count number of lines changed, by insertions and deletions.
        :return: int, number of lines changed
        """

        result_diff = subprocess.Popen(
            'cd target_repo && git diff --shortstat HEAD~3 HEAD',
            stdout=subprocess.PIPE,
            shell=True)

        diffs = str(result_diff.communicate()).split('\\n')[0]
        total = 0

        insertions = re.search(r"(\d+) insertions", diffs)
        deletions = re.search(r"(\d+) deletions", diffs)
        if insertions:
            total += int(insertions.group().split()[0])
        if deletions:
            total += int(deletions.group().split()[0])
        return total

    @staticmethod
    def get_folder_sizes():
        """
        Get folder sizes, down to depth of 2.
        :return:
        """
        def print_dir_size(dir_path):
            print(dir_path, " - ", os.path.getsize(dir_path) / 1000000, "MB")

        path = Path(os.getcwd()).joinpath('target_repo')
        for item in os.listdir(path):
            item_path = path.joinpath(item)

            if os.path.isdir(item_path):
                print_dir_size(item_path)

                for sub_item in os.listdir(item_path):
                    sub_item_path = item_path.joinpath(sub_item)

                    if os.path.isdir(sub_item_path):
                        print_dir_size(sub_item_path)



language = 'Python'
q5 = RepoStats("https://github.com/python/devguide.git")

print("Files:", q5.get_file_count(language))
print("Lines Total & Commented:", q5.get_lines_count(language))
print("Function count:", q5.get_function_count(language))
print("Line change count:", q5.get_linechange_count())
q5.get_folder_sizes()
# q5.delete_repo()
