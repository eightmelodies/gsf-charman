# Charman

## Overview

Charman (short for Character Manager) is a suite of tools that run and manage [Gemstone](https://gswiki.play.net) character sessions in [Lich](github.com/elanthia-online/lich-5). There are 3 components required for this all to work: 1) a daemon script that follows pre-configured rules to orchestrate chracter logon/logoff, 2) a Lich script that communicates character state and handles logoff requests, and 3) an API server that facilitates the communcation between the daemon and the Lich script.

## Components

### Daemon

Uses [python-systemd](https://github.com/systemd/python-systemd) to run as a user daemon. Launches the Lich proxies based on configuration and talks to the API server to request logouts when needed.

### Lich script

Should be added to Lich's autostart scripts. Periodically reads Lumnis and other data it sends back to the API server. When it receives a logoff request from the API server, handles getting the character into a safe state and quitting the game.

### API server

This is a very simple FastAPI server that stores and processes information the daemon and Lich script use. It has the following routes:
1. /characters/{name} - initial character creation, fetching character data
1. /characters/{name}/lumnis - populated from the Licht script, data about remaining Lumnis experience and weekly resource
1. /characters/{name}/pending-logout-requests - whether or not the Licht script should tidy things up and proceed with logging out

