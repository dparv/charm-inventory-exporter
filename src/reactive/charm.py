#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import logging

from charms.reactive import set_flag, when, when_not, hook, endpoint_from_flag
from charms.layer import snap
from charmhelpers.core import hookenv
from charmhelpers.core.host import service_running

logger = logging.getLogger(__name__)

@when_not("inventory-exporter.installed")
def install():
    """Install hook."""
    hookenv.status_set("maintenance", "Installing charm...")
    hookenv.open_port(8675, 'TCP')
    hookenv.status_set("active", "Unit is ready.")
    set_flag("inventory-exporter.installed") 

@when("config.changed")
def config_changed():
    hookenv.status_set("active", "Unit is ready.")

@hook("update-status")
def update_status():
    inventory_exporter_service = "snap.inventory-exporter.inventory-exporter"
    running = service_running(inventory_exporter_service)
    if not running:
        error = inventory_exporter_service + " service not running"
        hookenv.status_set("active", error)
        return
    hookenv.status_set("active", "Unit is ready.")

@hook("stop")
def stop():
    snap.remove("inventory-exporter")
