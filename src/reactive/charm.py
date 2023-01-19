#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import logging
import socket

from charms.reactive import set_flag, when, when_not, hook, clear_flag
from charms.layer import snap
from charmhelpers.core import hookenv
from charmhelpers.core.templating import render
from charmhelpers.core.host import service_running, service_restart

logger = logging.getLogger(__name__)


CONFIG_TEMPLATE = 'config.j2'
CONFIG_FILE = '/var/snap/inventory-exporter/common/config.yaml'
INVENTORY_EXPORTER_SERVICE = "snap.inventory-exporter.inventory-exporter"

@when_not("inventory-exporter.installed")
def install():
    """Install hook."""
    hookenv.status_set("maintenance", "Installing charm...")
    hookenv.status_set("active", "Unit is ready.")
    set_flag("inventory-exporter.installed") 

@when("config.changed")
def config_changed():
    """Config changed hook."""
    hookenv.open_port(hookenv.config("port"), 'TCP')
    clear_flag('inventory-exporter.config.rendered')
    hookenv.status_set("active", "Unit is ready.")

@when("config.changed.port")
def port_changed():
    for full_port in hookenv.opened_ports():
        port = full_port.split("/")[0]
        hookenv.close_port(port, 'TCP')
    hookenv.open_port(hookenv.config("port"), 'TCP')
    clear_flag('inventory-exporter.config.rendered')
    configure_inventory_exporter_relation()

@hook("update-status")
def update_status():
    """Update status hook."""
    running = service_running(INVENTORY_EXPORTER_SERVICE)
    if not running:
        error = INVENTORY_EXPORTER_SERVICE + " service not running"
        hookenv.status_set("blocked", error)
        return
    hookenv.status_set("active", "Unit is ready.")

@hook("stop")
def stop():
    """Stop hook."""
    snap.remove("inventory-exporter")

@hook('inventory-exporter-relation-joined', 'inventory-exporter-relation-changed')
def configure_inventory_exporter_relation(relation_id=None, unit=None):
    """Provide relation data."""
    relations = hookenv.relation_ids("inventory-exporter")
    if not relations:
        return
    local_unit_address = hookenv.unit_private_ip()
    relation_settings = {
        "port": hookenv.config('port'),
        "model": hookenv.model_name(),
        "hostname": socket.gethostname(),
    }
    for rid in relations:
        hookenv.relation_set(
            rid,
            relation_settings=relation_settings,
        )
    hookenv.status_set('active', 'Unit is ready.')

@when_not('inventory-exporter.config.rendered')
def render_config():
    """Render the exporter snap config."""
    context = {
        'bind_address': hookenv.config("bind_address"),
        'port': hookenv.config("port"),
        }
    render(
        source=CONFIG_TEMPLATE,
        target=CONFIG_FILE,
        context=context,
    )
    service_restart(INVENTORY_EXPORTER_SERVICE)
    set_flag('inventory-exporter.config.rendered')
