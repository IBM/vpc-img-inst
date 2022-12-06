import logging
import os
import re
import subprocess
import sys
import time
import uuid
from enum import Enum
from os.path import isfile, join
from vpc_img_inst.constants import USER_SCRIPTS_FOLDER

import ibm_cloud_sdk_core
import inquirer
import yaml
from vpc_img_inst.constants import DEFAULTS, DIR_PATH
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services import IamIdentityV1
from inquirer import errors

logging.basicConfig(level = logging.INFO,  format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
ARG_STATUS = Enum('STATUS', 'VALID INVALID MISSING')  # variable possible status.
CACHE = {}
class MSG_STATUS(Enum):
    ERROR = '[ERROR]'
    WARNING = '[WARNING]'
    SUCCESS = '[SUCCESS]'

NEW_INSTANCE = 'Create a new'  # guaranteed substring in every 'create new instance' option prompted to user.


def get_option_from_list(msg, choices, default=None, choice_key='name', do_nothing=None, validate=True, carousel=True):
    """returns the user's choice out of given 'choices'. 
        :param msg - msg to display the user before presenting choices
        :param choices - list of choices to present user with
        :param default - default choice out of the lists of choices presented to user
        :param choice_key - if 'choices' is a dict `choice_key` represents the key associated with the desired values
        :param do_nothing:str - an additional choice for 'choices' to be appended to the list
        :param carousel - when set to true allows user to rotate from last to first choice and vice-a-versa    """
    if (len(choices) == 0 and do_nothing == None):
        error_msg = f"There no option for {msg}"
        print(error_msg)
        raise Exception(error_msg)

    if (len(choices) == 1 and not do_nothing):
        return (choices[0])

    if choice_key:
        choices_keys = [choice[choice_key] for choice in choices]
    else:
        choices_keys = [choice for choice in choices]

    if do_nothing:
        choices_keys.insert(0, do_nothing)

    questions = [
        inquirer.List('answer',
                      message=msg,
                      choices=choices_keys,
                      default=default,
                      validate=validate,
                      carousel=carousel,
                      ), ]
    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)

    # now find the object by name in the list
    if answers['answer'] == do_nothing:
        return do_nothing
    else:
        if choice_key:
            return next((x for x in choices if x[choice_key] == answers['answer']), None)
        else:
            return next((x for x in choices if x == answers['answer']), None)


def inquire_user(msg, choices, default=None, choice_key='name', create_new_instance=None,
                 handle_strings=False, validate=True, carousel=True):
    
    """returns the user's choice out of given 'choices'. 
      :param str create_new_instance: when initialized adds a 'create' option that allows the user
                            to create an instance rather than to opt for one of the options.
      :param bool handle_strings: when set to True handles input of list of strings instead of list of dicts.
      :param str choice_key: creates options list presented to user (choices_keys) using this key """

    # options to be displayed to user
    choices_keys = [choice[choice_key] for choice in choices] if not handle_strings else choices

    if create_new_instance:
        choices_keys.insert(0, color_msg(create_new_instance, style=Style.ITALIC))

    if len(choices_keys) == 0:
        raise Exception(f"No options were found to satisfy the following request: {msg}")

    if len(choices_keys) == 1:
        if create_new_instance:
            print(color_msg(f"\nNo existing instances were found in relation to the request: "
                            f"'{msg}'. Create a new one to proceed. ", color=Color.RED))
        else:
            print(color_msg(f"single option was found in response to the request: '{msg}'."
                            f" \n{choices[0]} was automatically chosen\n", color=Color.LIGHTGREEN))
            return choices[0]

    questions = [
        inquirer.List('answer',
                      message=msg,
                      choices=choices_keys,
                      default=default,
                      validate=validate,
                      carousel=carousel,
                      )]
    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)

    if create_new_instance and create_new_instance in answers['answer']:
        return create_new_instance
    elif handle_strings:  # returns the string the user chose
        return answers['answer']
    else:  # returns the object belonging to user's choice
        return next((x for x in choices if x[choice_key] == answers['answer']), None)

def find_obj(objects, msg, obj_id=None, obj_name=None, default=None, do_nothing=None):
    """returns object matching the specified keys' values: obj['id'] or obj['name']. Else, returns a user chosen object.   
    obj_id and obj_name are the values for: 'id' and 'name' - common keys in the API response format of IBM SDK.
    """
    obj = None
    if obj_id:
        # validating that obj exists
        obj = next((obj for obj in objects if obj['id'] == obj_id), None)
        if not obj:
            raise Exception(f'Object with specified id {obj_id} not found')
    if obj_name:
        obj = next((obj for obj in objects if obj['name'] == obj_name), None)
    
    if not obj:  # no matching values were found, collecting user's choice from 'objects'.
        obj = get_option_from_list(
            msg, objects, default=default, do_nothing=do_nothing)
    return obj

def find_name_id(objects, msg, obj_id=None, obj_name=None, default=None, do_nothing=None):
    obj = find_obj(objects, msg, obj_id, obj_name, default, do_nothing)
    if do_nothing and obj == do_nothing:
        return None, None

    return obj['name'], obj['id']

def validate_not_empty(answers, current):
    if not current:
        raise errors.ValidationError('', reason=f"Key name can't be empty")
    return True


def validate_exists(answers, current):
    if not current or not os.path.exists(os.path.abspath(os.path.expanduser(current))):
        raise errors.ValidationError(
            '', reason=f"File {current} doesn't exist")
    return True


def get_region_by_endpoint(endpoint):
    return re.search('//(.+?).iaas.cloud.ibm.com', endpoint).group(1)


def find_default(template_dict, objects, name=None, id=None, substring=False):
    """returns an object in 'objects' who's value for the field 'name' or 'id' equals that of item[name]/item[id] for an item in template_dict

    Args:
        template_dict (dict): dict from an existing configuration file that may contain desired values. 
        objects (list of dicts): list of dicts that may contain a key with the desired value.  
        name (str): name of the key of an object within 'template_dict' that contains the desired value, to be evaluated against obj['name'] of 'objects'.
        id (str): name of the key of an object within 'template_dict' that contains the desired value, to be evaluated against obj['id'] of 'objects'
        substring (bool): if set to true, the substring value of the desired val in template_dict is tested against the value of 'objects' 
    """

    val = None
    for k, v in template_dict.items():
        if isinstance(v, dict):
            return find_default(v, objects, name=name, id=id)
        else:
            if name:
                key = 'name'
                if k == name:
                    val = v
            elif id:
                key = 'id'
                if k == id:
                    val = v

            if val:
                if not substring:
                    obj = next((obj for obj in objects if obj[key] == val), None)
                else:
                    obj = next((obj for obj in objects if val in obj[key]), None)
                if obj:
                    return obj['name']


def free_dialog(msg, default=None, validate=True):
    """ Returns user's answer to an open-ended question """
    question = [
        inquirer.Text('answer',
                      message=msg,
                      default=default,
                      validate=validate)]
    answer = inquirer.prompt(question, raise_keyboard_interrupt=True)
    return answer


def password_dialog(msg, default=None, validate=True):
    question = [
        inquirer.Password('answer',
                          message=msg,
                          default=default,
                          validate=validate)]
    answer = inquirer.prompt(question, raise_keyboard_interrupt=True)
    return answer


def get_confirmation(msg, default=None):
    questions = [
        inquirer.Confirm('answer',
                         message=msg,
                         default=default,
                         ), ]
    answer = inquirer.prompt(questions, raise_keyboard_interrupt=True)

    return answer


def retry_on_except(retries, sleep_duration, error_msg='', default=None):
    """A decorator that calls the decorated function up to a number of times equals to 'retires' with a given
      'sleep_duration' in between.
       if the function failed the allotted number of retries, a default value will be returned,
       granted that one was provided, else the config tool will be terminated. """

    def retry_on_except_warpper(func):
        def func_wrapper(*args, **kwargs):
            msg = error_msg  # transferring the value via a mediator is necessary due to decorator's restrictions.
            for retry in range(retries):
                try:
                    result = func(*args, **kwargs)
                    return result

                except Exception as e:
                    msg += str(e)
                    if retry < retries - 1:  # avoid sleeping after last failure
                        time.sleep(sleep_duration)
            if default:
                print(color_msg(f"{msg}", color=Color.RED))
                return default
            else:
                print(color_msg(f"{msg}\nConfig tool was terminated", color=Color.RED))
                sys.exit(1)

        return func_wrapper

    return retry_on_except_warpper


def run_cmd(cmd):
    """runs a command via cli while constantly printing the output from the read pipe"""

    # small buffer size forces the process not to buffer the output, thus printing it instantly.
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, shell=True)
    for line in iter(process.stdout.readline, b''):
        print(line.decode())
    process.stdout.close()
    process.wait()

def verify_paths(input_path, output_path):
    """:returns a valid input and output path files, in accordance with provided paths.
        if a given path is invalid, and user is unable to rectify, a default path will be chosen in its stead. """

    def _is_valid_input_path(path):
        if not os.path.isfile(path):
            print(color_msg(f"\nError - Path: '{path}' doesn't point to a file. ", color=Color.RED))
            return False
        return True

    def _is_valid_output_path(path):
        """:returns path if it's either a valid absolute path, or a file name to be appended to current directory"""
        dir_file = path.rsplit(os.sep, 1)
        prefix_directory = dir_file[0]
        if len(dir_file) == 1 or os.path.isdir(prefix_directory):
            return path
        else:
            print(color_msg(f"{prefix_directory} doesn't lead to an existing directory", color=Color.RED))

    if not input_path or not _is_valid_input_path(input_path):
        input_path = DEFAULTS['input_file']
    if not output_path or not _is_valid_output_path(output_path):
        output_file = get_unique_file_name("created_resources",DEFAULTS['output_folder'])
    else:
        output_file = get_unique_file_name("created_resources",output_path)

    return input_path, output_file


def verify_iam_api_key(answers, apikey, iam_endpoint=None):
    """Terminates the config tool if no IAM_API_KEY matching the provided value exists"""

    iam_identity_service = IamIdentityV1(authenticator=IAMAuthenticator(apikey, url=iam_endpoint))
    try:
        iam_identity_service.get_api_keys_details(iam_api_key=apikey)
    except ibm_cloud_sdk_core.api_exception.ApiException:
        raise errors.ValidationError('', reason=color_msg(f"No IAmApiKey matching the given value {apikey} was found.", Color.RED))
    return True

def color_msg(msg, color=None, style=None, background=None):
    """reformat a given string and returns it, matching the desired color,style and background in Ansi color code.
        parameters are Enums of the classes: Color, Style and Background."""

    init = '\033['
    end = '\033[m'
    font = ''
    if color:
        font += color.value
    if style:
        font = font + ';' if font else font
        font += style.value

    if background:
        font = font + ';' if font else font
        font += background.value

    return init + font + 'm' + msg + end


class Color(Enum):
    BLACK = '30'
    RED = '31'
    GREEN = '32'
    BROWN = '33'
    BLUE = '34'
    PURPLE = '35'
    CYAN = '36'
    LIGHTGREY = '37'
    DARKGREY = '90'
    LIGHTRED = '91'
    LIGHTGREEN = '92'
    YELLOW = '93'
    LIGHTBLUE = '94'
    PINK = '95'
    LIGHTCYAN = '96'


class Style(Enum):
    RESET = '0'
    BOLD = '01'
    DISABLE = '02'
    ITALIC = '03'
    UNDERLINE = '04'
    REVERSE = '07'
    STRIKETHROUGH = '09'


class Background(Enum):
    BLACK = '40'
    RED = '41'
    GREEN = '42'
    ORANGE = '43'
    BLUE = '44'
    PURPLE = '45'
    CYAN = '46'
    LIGHTGREY = '47'

def get_unique_file_name(name, path):
    """returns the path to a file holding a unique name within the specified path"""
    if path[-1] != os.sep:
        path += os.sep
    files = [f for f in os.listdir(path) if isfile(join(path, f))] # files in directory

    return path + get_unique_name(name, files)

def get_unique_name(name, name_list):
    unique_name = name
    c = 1
    while unique_name in name_list:    # find next default available vpc name
        unique_name = f'{name}-{c}'
        c += 1
    return unique_name

def store_output(data:dict, config):
    with open(config['output_file'], 'a') as file:
        yaml.dump(data, file, default_flow_style=False)

def append_random_suffix(base_name:str):
    """appends a unique suffix (minimum length of 10 chars) to VPC resources"""
    min_chars_to_append = 10
    max_length = 62  # max length allowed for naming ibm resources is 63. separating the random part with a '-' decreases it to 62.    
    suffix = str(uuid.uuid4())
    if len(base_name) + len(suffix) > max_length: 
        # appends the last 10 chars of suffix to the first 51 chars of base_name with a dash in between. 
        return base_name[:max_length-min_chars_to_append] + '-' + suffix[-min_chars_to_append:]
    else:
        return base_name + '-' + suffix

def create_folders(): 
    if not os.path.exists(USER_SCRIPTS_FOLDER):
        os.makedirs(USER_SCRIPTS_FOLDER)

def get_supported_features():
    project_path = DIR_PATH+os.sep+"installation_scripts"
    project_features = [feature for feature in next(os.walk(project_path))[1]]
    user_features = [feature for feature in next(os.walk(USER_SCRIPTS_FOLDER))[1]]
    return set(project_features + user_features)

def get_installation_types_for_feature(feature):
    """
    returns a dict in the key:val format of installation_type_name:path_to_script 
    Note: installation scripts in user's scripts folder (USER_SCRIPTS_FOLDER) will override similarly named scripts for the same feature, 
          found in the project's scripts folder.
    """

    def _get_scripts(feature_path):
        """populates inst_types with scripts belonging to the specified feature"""
        if os.path.exists(feature_path):
            # collect file names under the feature folder 
            feature_script_files = [f for f in os.listdir(feature_path) if isfile(join(feature_path, f))]  #  e.g. install_docker_rhel.sh
            # extract installation type names from above feature_script_files
            inst_types = [file[file.rfind('_')+1:file.rfind('.')] for file in feature_script_files]  #  e.g. rhel

            for inst_name,path in [*zip(inst_types,feature_script_files)]:
                
                matching_scripts_path[inst_name] = feature_path+os.sep+path

    matching_scripts_path = {}
    user_feature_scripts_path = USER_SCRIPTS_FOLDER+os.sep+feature
    project_feature_scripts_path = DIR_PATH+os.sep+"installation_scripts"+os.sep+feature

    _get_scripts(project_feature_scripts_path)
    _get_scripts(user_feature_scripts_path)

    return matching_scripts_path