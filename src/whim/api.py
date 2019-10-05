import atomicwrites


class EditorAPI(object):
    def __init__(self):
        pass

    def read_file(self, file_path):
        try:
            with open(file_path) as f:
                content = f.read()
        except FileNotFoundError:
            content = ''
        return {
            'file_content': content,
        }

    def write_file(self, file_path, file_content):
        with atomicwrites.atomic_write(file_path, overwrite=True) as f:
            f.write(file_content)
