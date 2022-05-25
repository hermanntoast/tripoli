#!/usr/bin/env python3

import gi
import os
import threading
import time
import logging

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk as gtk, AppIndicator3 as appindicator, GLib

scriptPath = os.path.expanduser("~") + "/.config/tripoli/"
logPath = os.path.expanduser("~") + "/.config/tripoli/log/"

logging.basicConfig(filename=logPath + 'tripoli.log', format='%(levelname)s: %(asctime)s %(message)s', level=logging.INFO)

def __execute(command) -> list:
    commandline = ""
    for cmd in command:
        commandline += str(cmd) + " "
    stream = os.popen(commandline)
    return stream.read().splitlines()

def getScriptsFromDirectory() -> list:
    scriptList = list()
    for filename in os.listdir(scriptPath):
        if ".sh" in filename:
            scriptList.append(filename)
    return scriptList

def getPluginConfig(script):
    with open(scriptPath + script) as f:
        started = False
        config = dict()
        for line in f.readlines():
            if "##### PLUGININFO #####" in line:
                started = True if started == False else False
                continue
            if started:
                line = line.replace("#", "").replace("\n", "").strip().split("=")
                config[line[0].strip()] = line[1].strip()
    return config

def menu(script):
    logging.debug("Execute script " + script + "...")
    menu = gtk.Menu()

    scriptResult = __execute([scriptPath + script])
    for line in scriptResult:
        if "---" in line:
            menuentry = gtk.SeparatorMenuItem()
            menu.append(menuentry)
        else:
            menuentry = gtk.ImageMenuItem(label=line)
            menu.append(menuentry)

    logging.debug("Script " + script + " finished!")
    menu.show_all()

    return menu

def start(script):
    pluginConfig = getPluginConfig(script)
    indicator = appindicator.Indicator.new(pluginConfig["PLUGIN_NAME"], pluginConfig["PLUGIN_ICON"], appindicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

    def start():
        logging.info("Start/Restart menu creation for " + script + "...")
        indicator.set_menu(menu(script))
        return GLib.SOURCE_CONTINUE

    GLib.timeout_add_seconds(int(pluginConfig["PLUGIN_INTERVAL"]), start)
    start()
    
    gtk.main_iteration_do(True)
    gtk.main()

def main():
    threadList = list()
    for script in getScriptsFromDirectory():
        thread = threading.Thread(target=start, args=(script,))
        thread.start()
        threadList.append(thread)

    while True:
        for thread in threadList:
            if thread.is_alive():
                logging.debug("Thread " + str(thread) + " is still running!")
        time.sleep(5)

if __name__ == "__main__":
    try:
        logging.info("Starting application...")
        main()
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        logging.critical(e)
        pass
    finally:
        logging.info("Stopping application...")