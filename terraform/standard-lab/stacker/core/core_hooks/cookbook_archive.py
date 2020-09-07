"""Handles tasks related to cookbook archives."""

from contextlib import contextmanager
from subprocess import check_call

import gzip
import io
import logging
import os
import re
import tarfile

from distutils.version import LooseVersion

from stacker.session_cache import get_session
from stacker.util import get_config_directory

import stacker
LEGACY_STACKER = LooseVersion(stacker.__version__) < LooseVersion('1.6.0')
LEGACY_STACKER_PRE_121 = LooseVersion(stacker.__version__) < LooseVersion('1.2.1')  # noqa
if LEGACY_STACKER:
    from stacker.lookups.handlers.default import handler as default_handler  # noqa pylint: disable=no-name-in-module,line-too-long
    from stacker.lookups.handlers.output import handler as output_handler  # noqa pylint: disable=no-name-in-module,line-too-long
    if not LEGACY_STACKER_PRE_121:
        from stacker.lookups.handlers.xref import handler as xref_handler  # noqa pylint: disable=no-name-in-module,line-too-long
else:
    from stacker.lookups.handlers.output import OutputLookup  # noqa pylint: disable=no-name-in-module,line-too-long
    from stacker.lookups.handlers.xref import XrefLookup  # noqa pylint: disable=no-name-in-module,line-too-long
    from stacker.lookups.handlers.default import DefaultLookup  # noqa pylint: disable=no-name-in-module,line-too-long
    default_handler = DefaultLookup.handle  # noqa
    output_handler = OutputLookup.handle  # noqa
    xref_handler = XrefLookup.handle  # noqa

LOGGER = logging.getLogger(__name__)
COOKBOOK_PKG_PATTERN = re.compile(r'^cookbooks-[0-9]*\.(tar\.gz|tgz)')


@contextmanager
def change_dir(newdir):
    """Change directory.

    Adapted from http://stackoverflow.com/a/24176022

    """
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def get_cookbook_archive_filename(path):
    """Find highest numbered cookbook archive file in `path`.

    Args:
        path (str): Filesystem path

    Returns: string of filename

    """
    for i in sorted(os.listdir(path), reverse=True):
        if COOKBOOK_PKG_PATTERN.match(i):
            return i


def purge_cookbook_archives(path):
    """Remove all cookbook archives from `path`.

    Args:
        path (str): Filesystem path

    """
    for i in os.listdir(path):
        if COOKBOOK_PKG_PATTERN.match(i):
            LOGGER.info("Deleting existing local cookbook archive %s.", i)
            os.remove(os.path.join(path, i))


def add_dir_to_archive(archive_path, directory):
    """Add a directory to an archive.

    Args:
        archive_path (str): Path to tgz
        directory (str): Filesystem path of directory to be added

    """
    LOGGER.info('Adding directory at path %s to cookbook archive at path %s.',
                directory, archive_path)
    if archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        # Uncompress the file to allow tarfile to append to it
        with gzip.open(archive_path) as fileobj:
            tar_in_mem = io.BytesIO(fileobj.read())
        with open(archive_path, 'wb') as fileobj:
            fileobj.write(tar_in_mem.read())
        tar_in_mem.close()
    archive = tarfile.open(archive_path, 'a')
    archive.add(directory, arcname=os.path.basename(directory))
    archive.close()
    with open(archive_path, 'rb') as fileobj:
        tar_in_mem = io.BytesIO(fileobj.read())

    with gzip.open(archive_path, 'wb') as fileobj:
        fileobj.write(tar_in_mem.read())


def package_and_upload(provider, context, **kwargs):  # pylint: disable=W0613
    """Ensure a cookbook archive is present on S3.

    Args:
        provider (:class:`stacker.providers.base.BaseProvider`): provider
            instance
        context (:class:`stacker.context.Context`): context instance

    Returns: boolean for whether or not the hook succeeded.

    """
    always_upload_new_archive = kwargs.get('always_upload_new_archive', False)
    environment = kwargs.get('environment', 'common')
    cookbook_relative_path = default_handler(
        kwargs.get('cookbook_relative_path_default'),
        provider=provider,
        context=context
    )
    cookbook_path = os.path.normpath(
        os.path.join(os.path.abspath(get_config_directory()),
                     cookbook_relative_path)
    )
    LOGGER.debug("cookbook path found to be %s.", cookbook_path)
    if kwargs.get('chef_config_bucket_output'):
        chef_config_bucket = output_handler(
            kwargs.get('chef_config_bucket_output'),
            provider=provider,
            context=context
        )
    else:
        if LEGACY_STACKER_PRE_121:
            chef_config_bucket = output_handler(
                kwargs.get('chef_config_bucket_xref'),
                provider=provider,
                context=context,
                fqn=True
            )
        else:
            chef_config_bucket = xref_handler(
                kwargs.get('chef_config_bucket_xref'),
                provider=provider,
                context=context,
            )
    bucket_key = default_handler(
        kwargs.get('s3_bucket_key_default'),
        provider=provider,
        context=context
    )
    bucket_prefix = '%s/%s' % (environment, bucket_key)

    session = get_session(provider.region)
    client = session.client('s3')

    if always_upload_new_archive is False:
        list_results = client.list_objects(
            Bucket=chef_config_bucket,
            Prefix='%s/cookbooks-' % bucket_prefix
        )
        if 'Contents' in list_results:
            LOGGER.info('Skipping cookbook upload; archive already present '
                        'on S3.')
            return True
    # Before creating a fresh cookbook archive, ensure no existing ones are
    # present (as they'll be duplicated in the archive)
    purge_cookbook_archives(cookbook_path)

    # Generate the cookbook archive
    with change_dir(cookbook_path):
        check_call(['berks', 'package', '--except=integration'])

    # Find the archive filename
    cookbook_archive = get_cookbook_archive_filename(cookbook_path)

    # Add any additional directories (e.g. data_bags) to the archive
    if kwargs.get('additional_dirs_relative_paths'):
        for i in kwargs.get('additional_dirs_relative_paths'):
            add_dir_to_archive(
                os.path.join(cookbook_path, cookbook_archive),
                os.path.normpath(
                    os.path.join(os.path.abspath(get_config_directory()), i)
                ))

    LOGGER.info('Uploading archive %s to s3://%s/%s/',
                cookbook_archive,
                chef_config_bucket,
                bucket_prefix)
    client.put_object(Body=open(os.path.join(cookbook_path,
                                             cookbook_archive), 'rb'),
                      Bucket=chef_config_bucket,
                      Key='%s/%s' % (bucket_prefix, cookbook_archive))
    return True
