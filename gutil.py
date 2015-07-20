import configparser,glob,os

def get_image_path():
    _BASE_PATH = os.path.split(os.path.realpath(__file__))[0]
    return os.path.join(_BASE_PATH,'images')

def get_config():
    config = configparser.ConfigParser()
    if not glob.glob("*.conf"):
        # use default config
        configfile=os.path.join(os.path.dirname(__file__),'default.conf')
    else:
        configfile = os.path.join(os.getcwd(),glob.glob("*.conf")[0])
    config.read(configfile)
    return config