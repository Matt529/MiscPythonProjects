import sys
import os
import json
import zipfile

MOD_INFO_FILENAME = "mcmod.info"
DEFAULT_WORKING_DIR = "./mods"

work_dir = None
output_file = None
mod_pack_name = None
mod_pack_mcversion = None

'''
    A Representation of a Mod's MCMod.info file and information grabbed from it.
'''
class MCModInfo:

    """
        Attempts to Populate the 'Info Map' to use in the get(key) function
    """
    def compile_map(self, zip_file=None):
        if zip_file is None:
            self.info_map.setdefault("author", "Unknown" if self.authors is None      # Primary Author
                                     or len(self.authors) == 0 else self.authors[0])  # or Unknown
            self.info_map.setdefault("authors", self.authors)                         # All Authors & Contributors
            self.info_map.setdefault("name", self.mod_name)                           # Mod Name
            self.info_map.setdefault("version", self.mod_version)                     # Mod Version
            self.info_map.setdefault("mcversion", self.mod_mcversion)                 # Supported Minecraft Version
            self.info_map.setdefault("desc", self.mod_desc)                           # Mod Description
            self.info_map.setdefault("description", self.mod_desc)                    # Mod Description Alias
            self.info_map.setdefault("url", self.mod_url)                             # Mod URL If Provided
        else:
            # Set All to None if no MCMod.info file is found... simply print the Zip filename
            self.info_map.setdefault("author", None)
            self.info_map.setdefault("authors", None)
            self.info_map.setdefault("name", zip_file[zip_file.rindex("/") + 1:])
            self.info_map.setdefault("version", None)
            self.info_map.setdefault("mcversion", None)
            self.info_map.setdefault("desc", None)
            self.info_map.setdefault("description", None)
            self.info_map.setdefault("url", None)

    '''
        A conveniet "get" method for the JSON Table.

        If an attempt to access a key fails, None is returned and an error messaged printed.
    '''
    def get_from_json(self, key):
        try:
            return self.json_table[0][key]
        except KeyError:
            print("ERROR: {} did not exist in this mcmod.info file!".format(key))
            return None
        except TypeError:
            print("ERROR: No JSON File Loaded...")
            return None

    '''
        Load JSON Table and assign instance variables

        If JSON fails or a zip file is passed, simply use
        the ZipFile filename for the Mod Name and default
        the rest to None.
    '''
    def load(self, info_file, zip_file, is_zip=False):
        if not is_zip:
            try:
                # Attempt to Load JSON Table
                self.json_table = json.load(info_file)
                self.json_loaded = True
            except ValueError, e:
                # If Failed, Print Error and call back to Zip File method
                print("ERROR: VALUE " + e.message)
                self.load(info_file, zip_file, True)


            # If Loaded Successfully
            if self.json_loaded:
                self.authors = self.get_from_json('authorList')

                if self.authors is None:    # Account for some modders using 'authors' instead of 'authorList'
                    print("Attempting to use 'authors' instead of 'authorList'")
                    self.authors = self.get_from_json('authors')

                self.mod_name = self.get_from_json('name')
                self.mod_version = self.get_from_json('version')
                self.mod_mcversion = self.get_from_json('mcversion')
                self.mod_desc = self.get_from_json('description')
                self.mod_url = self.get_from_json('url')
                self.compile_map()
        else:   # Zip File Method
            name, ext = os.path.splitext(zip_file)
            self.compile_map(name)
            self.json_loaded = False

    '''
    A Constructor for a MCModInfo File

    Takes the MCModInfo File-like and ZipFile as requirements.
    If is_zip = True then the fallback Zip Method is done (refer to above)
    else the MCMod.info file is parsed normally.
    '''
    def __init__(self, info_file, zip_file, is_zip=False):

        ### INITIALIZE INSTANCE VARIABLES
        self.authors = []
        self.mod_name = None
        self.mod_version = None
        self.mod_mcversion = None
        self.mod_desc = None
        self.mod_url = None
        self.json_table = None
        self.json_loaded = True
        self.info_map = {}

        self.load(info_file, zip_file, is_zip)

    '''
        Gets the Primary Author (self.authors[0])
    '''
    def get_primary_author(self):
        return self.authors[0]

    '''
        Gets all Authors and Contributors as a single string
    '''
    def get_all_authors(self):
        full_team = ""
        for author in self.authors:
            if full_team == "":
                full_team += author
            else:
                full_team += ", {}".format(author)

        for contributor in self.get_from_json('credits'):
            full_team += ", {}".format(contributor)
        return full_team

    '''
        Convenience Method for getting a variable from the InfoMap.

        Returns either the value if it exists or N/A if it does not.
    '''
    def get(self, key):
        return self.info_map.get(key, "N/A")

    '''
        "To String" method accounting for the 3 states.

        1. Success
        2. Fallback to Zip Method
        3. Complete Failure
    '''
    def __str__(self):
        if self.json_loaded:
            name = self.get("name")
            author = self.get("author")
            version = self.get("version")
            desc = self.get("desc")
            url = self.get("url")
            team = ("Credit: " + self.get_all_authors() + "\n")\
                    if self.authors is not None and len(self.authors) > 1 else\
                    ""

            return "{} | Authored By: {} :: v{}\n" \
                   "{}\n" \
                   "{}\n" \
                   "{}".format(name, author, version, desc, url, team)
        elif self.get('name') is not None:
            return "\n" + self.get("name") + "\nNo mcmod.info File Was Found! Let the Dev Know!\n\n"
        else:
            return "Invalid JSON for Mod! This is VERY Unexpected..."

    def __repr__(self):
        name = self.get('name')
        if name is not None:
            return name + " MCModInfo"
        else:
            return "unknown"


"""
    Parses the Working Directory Argument. If it is valid,
    then that is returned. Else a default value is returned.

    Can be Relative or Absolute.

    If None is provided, "./mods" is returned
    If ./mods does not exist then None is returned.
"""
def initialize():
    global work_dir
    global output_file
    global mod_pack_name
    global mod_pack_mcversion

    default_exists = os.path.exists(DEFAULT_WORKING_DIR)

    if len(sys.argv) < 3:
        print("INVALID ARGUMENTS!")
        print("ModLister.py <modpack-name> <minecraft-version> [<output-file>] [root-directory]")
        print("The Root Directory Must contain a 'mods' folder!")
        print("Or, if no argument is passed, the current directory is used.")
        print("If no output-file is specified, it is spit out to the console.")
    else:
        mod_pack_name = sys.argv[1]
        mod_pack_mcversion = sys.argv[2]

        if len(sys.argv) >= 4:
            output_file = sys.argv[3]
        else:
            print("INVALID Output File! -- " + sys.argv[3])

        if len(sys.argv) >= 5 and os.path.exists(sys.argv[4]):
            work_dir = sys.argv[4]
        elif default_exists:
            work_dir = DEFAULT_WORKING_DIR
        else:
            work_dir = None

'''
    A Default Checker Function. May change in the future.

    Currently only allows JAR's and ZIP's
'''
def default_allow(suffix):
    if suffix == '.jar' or suffix == '.zip':
        return True
    else:
        return False


'''
    Get all Mod Files found in the ./mods folder
'''
def get_mods(root, check=default_allow):
    mod_files = []

    for mod_file in os.listdir(root):
        mod_file = root + "/" + mod_file
        if os.path.isfile(mod_file):
            print(mod_file + " is file")
            name, ext = os.path.splitext(mod_file)
            if check(ext):
                mod_files.append(mod_file)
            else:
                print(mod_file + " is NOT a Mod File... Bleh...")
        else:
            print(mod_file + " is dir")
            mod_files += get_mods(mod_file, check)[:]

    return mod_files


'''
    Compile all provided mod files into MCModInfo objects
'''
def compile_mod_info(mod_files):
    mc_info = []
    for mod in mod_files:
        found = False
        print(mod)
        mod_zip = zipfile.ZipFile(mod)
        for name in mod_zip.namelist():
            if name == MOD_INFO_FILENAME:
                mc_mod_info = mod_zip.open(name)
                mc_info.append(MCModInfo(mc_mod_info, mod))
                mc_mod_info.close()
                found = True
                break

        if not found:
            mc_info.append(MCModInfo(None, mod, True))
        mod_zip.close()

    return mc_info


'''
    Output's all provided MCModInfo objects to either Standard Out or a File
'''
def print_mod_info(modinfo, out=None):
    if out is None:
        for info in modinfo:
            print(str(info))
    else:
        out_file = open(out, 'w')
        out_file.write("########################################################################\n")
        out_file.write("Mod List Creator v1.0 by Matthew Crocco -- Written in Python :D")
        out_file.write("\n########################################################################")
        out_file.write("\nTotal Mods: " + str(len(modinfo)))
        out_file.write("\nModpack: " + mod_pack_name)
        out_file.write("\nMCVersion: " + mod_pack_mcversion)
        out_file.write("\n########################################################################\n")

        for info in modinfo:
            print("Writing " + repr(info) + " to " + out)
            out_file.write("\n########################################################################\n")
            out_file.write(str(info))
            out_file.write("########################################################################\n")
        out_file.close()

initialize()
print(work_dir)
if work_dir is not None:
    all_mods = get_mods(work_dir)
    print_mod_info(compile_mod_info(all_mods), output_file)
else:
    print("ERROR: Could Not Continue. No Mods File found in Root Directory!")