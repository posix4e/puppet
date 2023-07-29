---
title: puppet 
colorTo: indigo
app_file: backend/backend.py
sdk: gradio
sdk_version: 3.36.1
python_version: 3.11.2
pinned: false
license: mit
---
This attempts to recreate https://github.com/nat/natbot/blob/main/natbot.py but for android instead of the web. It uses acceesibility to see, and Android Intents to steer. Sometimes it needs the users' help because of android's security model. 


This is a 3 part system
- puppet can recieve commands and execute them. 
- backend which collects browser telemetry along with operating system telemetry at a fine grained level. Either android accesibility commands or web dom.
- client can be web but we also have a browser extension. Currently on for ios, but soon on all platforms.
# Deployment
- Here's my puppet backend https://posix4e-puppet.hf.space
# Planning 
We are using the github projects and issues features.
