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
        with open(file_path, 'w') as f:
            f.write(file_content)
