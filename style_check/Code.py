class Code:
    def __init__(self, source_name, source_file, language_extension):
        self.source_name = source_name
        self.source_file = source_file
        self.language_extension = language_extension

    def __str__(self):
        rep = ""
        rep += "source name: " + self.source_name + '\n'
        rep += "source_file: " + self.source_file + '\n'
        rep += "language extension: " + self.language_extension + '\n'

        return rep
