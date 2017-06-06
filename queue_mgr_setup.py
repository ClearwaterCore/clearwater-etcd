# @file queue_mgr_setup.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import logging
import sys
import multiprocessing

from setuptools import setup, find_packages

setup(
    name='clearwater-queue-manager',
    version='1.0',
    namespace_packages = ['metaswitch'],
    packages=['metaswitch', 'metaswitch.clearwater', 'metaswitch.clearwater.queue_manager'],
    package_dir={'':'src'},
    package_data={
        '': ['*.eml'],
        },
    test_suite='metaswitch.clearwater.queue_manager.test',
    install_requires=[
        "clearwater_etcd_shared",
        "metaswitchcommon"],
    tests_require=[
        "funcsigs==1.0.2",
        "Mock==2.0.0",
        "pbr==1.6",
        "six==1.10.0"]
    )
