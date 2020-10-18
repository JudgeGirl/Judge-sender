import yaml

class Config:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = yaml.load(f.read())

    def __getitem__(self, key):
        return self.config[key]
