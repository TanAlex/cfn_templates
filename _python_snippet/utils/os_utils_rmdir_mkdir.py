import os
import shutil


def make_dir(directory, logger=None):
    """Creates a directory if it doesn't exist.
       print message for command line use or else
       write messege to logger as applicable.
    Args:
        directory: string. directory name
        logger: instance of logger class. default none. optional
    """
    # if exist skip else create dir
    try:
        os.stat(directory)
        if logger is None:
            print("\n Directory {} already exist... skipping"
                  .format(directory))
        else:
            logger.info("Directory {} already exist... skipping"
                        .format(directory))
    except OSError:
        if logger is None:
            print("\n Directory {} not found, creating now..."
                  .format(directory))
        else:
            logger.info("Directory {} not found, creating now..."
                        .format(directory))
        os.makedirs(directory)


def remove_dir(directory, logger=None):
    """Creates a directory if it doesn't exist.
       print message for command line use or else
       write messege to logger as applicable.
    Args:
        directory: string. directory name
        logger: instance of logger class. default none. optional
    """
    # if exist skip else create dir
    try:
        os.stat(directory)
        if logger is None:
            print("\n Directory {} already exist, deleting open-source"
                  " directory".format(directory))
        else:
            logger.info("\n Directory {} already exist, deleting open-source"
                        " directory".format(directory))
        shutil.rmtree(directory)
    except OSError:
        if logger is None:
            print("\n Directory {} not found... nothing to delete"
                  .format(directory))
        else:
            logger.info("Directory {} not found... nothing to delete"
                        .format(directory))